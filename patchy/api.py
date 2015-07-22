# -*- encoding:utf-8 -*-
import inspect
import subprocess
import os
import shutil
from functools import wraps
from tempfile import mkdtemp
from textwrap import dedent

import pylru
import six

__all__ = ('patch', 'unpatch', 'temp_patch')


# Public API

def patch(func, patch_text):
    return _do_patch(func, patch_text, forwards=True)


def unpatch(func, patch_text):
    return _do_patch(func, patch_text, forwards=False)


class temp_patch(object):
    def __init__(self, func, patch_text):
        self.func = func
        self.patch_text = patch_text

    def __enter__(self):
        patch(self.func, self.patch_text)

    def __exit__(self, _, __, ___):
        unpatch(self.func, self.patch_text)

    def __call__(self, decorable):
        @wraps(decorable)
        def wrapper(*args, **kwargs):
            with self:
                decorable(*args, **kwargs)

        return wrapper


# Gritty internals

def _do_patch(func, patch_text, forwards):
    source = _get_source(func)
    patch_text = dedent(patch_text)

    source = _apply_patch(source, patch_text, forwards, func.__name__)

    # Recompile
    _set_source(func, source)


def _get_source(func):
    try:
        if inspect.ismethod(func):
            if hasattr(func, '__func__'):
                # classmethod, staticmethod
                return func.__func__._patchy_the_source
            else:
                return func.im_func._patchy_the_source
        else:
            return func._patchy_the_source
    except AttributeError:
        source = inspect.getsource(func)
        source = dedent(source)
        return source


_patching_cache = pylru.lrucache(100)


def _apply_patch(source, patch_text, forwards, name):
    # Cached ?
    if (source, patch_text, forwards) in _patching_cache:
        return _patching_cache[(source, patch_text, forwards)]

    # Write out files
    tempdir = mkdtemp(prefix='patchy')
    try:
        source_path = os.path.join(tempdir, name + '.py')
        with open(source_path, 'w') as source_file:
            source_file.write(source)

        patch_path = os.path.join(tempdir, name + '.patch')
        with open(patch_path, 'w') as patch_file:
            patch_file.write(patch_text)
            if not patch_text.endswith('\n'):
                patch_file.write('\n')

        # Call `patch` command
        command = ['patch']
        if not forwards:
            command.append('--reverse')
        command.extend([source_path, patch_path])
        proc = subprocess.Popen(
            command,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        stdout, stderr = proc.communicate()

        if proc.returncode != 0:
            msg = "Could not {action} the patch {prep} '{name}'.".format(
                action=("apply" if forwards else "unapply"),
                prep=("to" if forwards else "from"),
                name=name
            )
            if stdout or stderr:
                msg += " The message from `patch` was:\n{}\n{}".format(
                    stdout.decode('utf-8'),
                    stderr.decode('utf-8')
                )
            msg += (
                "\nThe code to patch was:\n{}\nThe patch was:\n{}"
                .format(source, patch_text)
            )
            raise ValueError(msg)

        with open(source_path, 'r') as source_file:
            new_source = source_file.read()
    finally:
        shutil.rmtree(tempdir)

    # Cache in both directions - makes reversal faster
    _patching_cache[(source, patch_text, forwards)] = new_source
    other_direction = (not forwards)
    _patching_cache[(new_source, patch_text, other_direction)] = source

    return new_source


def _get_flags_mask():
    import __future__
    result = 0
    for name in __future__.all_feature_names:
        result |= getattr(__future__, name).compiler_flag
    return result

FEATURE_MASK = _get_flags_mask()


def _set_source(func, new_source):
    # Fetch the actual function we are changing
    if inspect.ismethod(func):
        try:
            # classmethod, staticmethod
            real_func = func.__func__
        except AttributeError:
            real_func = func.im_func
    else:
        real_func = func

    # Figure out any future headers that may be required
    feature_flags = real_func.__code__.co_flags & FEATURE_MASK

    # Compile and retrieve the new Code object
    localz = {}
    new_code = compile(
        new_source,
        '<patchy>',
        'exec',
        flags=feature_flags,
        dont_inherit=True
    )

    six.exec_(new_code, func.__globals__, localz)
    new_func = localz[func.__name__]

    # Figure out how to get the Code object
    if isinstance(new_func, (classmethod, staticmethod)):
        new_code = new_func.__func__.__code__
    else:
        new_code = new_func.__code__

    # Put the new Code object in place
    real_func.__code__ = new_code
    real_func._patchy_the_source = new_source
