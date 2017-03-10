# -*- encoding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import ast
import inspect
import os
import shutil
import subprocess
from functools import wraps
from tempfile import mkdtemp
from textwrap import dedent
from weakref import WeakKeyDictionary

import six

from .cache import PatchingCache

__all__ = ('patch', 'mc_patchface', 'unpatch', 'temp_patch')


# Public API

def patch(func, patch_text):
    return _do_patch(func, patch_text, forwards=True)


mc_patchface = patch


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

    new_source = _apply_patch(source, patch_text, forwards, func.__name__)

    _set_source(func, new_source)


_patching_cache = PatchingCache(maxsize=100)


def _apply_patch(source, patch_text, forwards, name):
    # Cached ?
    try:
        return _patching_cache.retrieve(source, patch_text, forwards)
    except KeyError:
        pass

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

    _patching_cache.store(source, patch_text, forwards, new_source)

    return new_source


def _get_flags_mask():
    import __future__
    result = 0
    for name in __future__.all_feature_names:
        result |= getattr(__future__, name).compiler_flag
    return result


FEATURE_MASK = _get_flags_mask()


# Stores the source of functions that have had their source changed
_source_map = WeakKeyDictionary()


def _get_source(func):
    real_func = _get_real_func(func)
    try:
        return _source_map[real_func]
    except KeyError:
        source = inspect.getsource(func)
        source = dedent(source)
        return source


def _class_name(func):
    qualname = getattr(func, '__qualname__', None)
    if qualname is not None:
        split_name = qualname.split('.')
        try:
            class_name = split_name[-2]
        except IndexError:
            return None
        else:
            if class_name == '<locals>':
                return None
            return class_name
    im_class = getattr(func, 'im_class', None)
    if im_class is not None:
        return im_class.__name__


def _set_source(func, func_source):
    # Fetch the actual function we are changing
    real_func = _get_real_func(func)
    # Figure out any future headers that may be required
    feature_flags = real_func.__code__.co_flags & FEATURE_MASK

    def _compile(code, flags=0):
        return compile(
            code,
            '<patchy>',
            'exec',
            flags=feature_flags | flags,
            dont_inherit=True,
        )

    class_name = _class_name(func)
    _def = 'def __patchy_freevars__():'
    fvs = func.__code__.co_freevars
    fv_body = ['    {0} = object()'.format(fv) for fv in fvs]
    _ast = _compile(func_source, ast.PyCF_ONLY_AST)
    if class_name:
        class_src = '    class {name}(object):\n        pass'.format(name=class_name)
        ret = '    return {name}'.format(name=class_name)
        to_parse = '\n'.join([_def] + fv_body + [class_src, ret])
        new_source = _compile(to_parse, ast.PyCF_ONLY_AST)
        new_source.body[0].body[-2].body[0] = _ast.body[0]
    else:
        ret = '    return {name}'.format(name=func.__name__)
        to_parse = '\n'.join([_def] + fv_body + ['    pass', ret])
        new_source = _compile(to_parse, ast.PyCF_ONLY_AST)
        new_source.body[0].body[-2] = _ast.body[0]

    # Compile and retrieve the new Code object
    localz = {}
    new_code = _compile(new_source)

    six.exec_(new_code, func.__globals__, localz)
    if class_name is not None:
        new_func = getattr(localz['__patchy_freevars__'](), func.__name__)
    else:
        new_func = localz['__patchy_freevars__']()

    # Figure out how to get the Code object
    if isinstance(new_func, (classmethod, staticmethod)):
        new_code = new_func.__func__.__code__
    else:
        new_code = new_func.__code__

    # Put the new Code object in place
    real_func.__code__ = new_code
    # Store the modified source. This used to be attached to the function but
    # that is a bit naughty
    _source_map[real_func] = func_source


def _get_real_func(func):
    """
    Duplicates some of the logic implicit in inspect.getsource(). Basically
    some function-esque things, such as classmethods, aren't functions but we
    can peel back the layers to the underlying function very easily.
    """
    if inspect.ismethod(func):
        return func.__func__
    else:
        return func
