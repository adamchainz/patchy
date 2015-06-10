# -*- encoding:utf-8 -*-
import inspect
import subprocess
import tempfile
import os
import shutil
from textwrap import dedent

import six

__all__ = ('patch', 'unpatch')


def patch(func, patch_text):
    return _do_patch(func, patch_text, forwards=True)


def unpatch(func, patch_text):
    return _do_patch(func, patch_text, forwards=False)


def _do_patch(func, patch_text, forwards):
    source = _get_source(func)
    patch_text = dedent(patch_text)

    # Write out files
    tempdir = tempfile.mkdtemp(prefix='patchy')
    try:
        source_path = os.path.join(tempdir, func.__name__ + '.py')
        with open(source_path, 'w') as source_file:
            source_file.write(source)

        patch_path = os.path.join(tempdir, func.__name__ + '.patch')
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
                name=func.__name__
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
            source = source_file.read()
    finally:
        shutil.rmtree(tempdir)

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


def _set_source(func, new_source):
    # Compile and retrieve the new Code object
    localz = {}
    six.exec_(new_source, func.__globals__, localz)
    new_func = localz[func.__name__]
    if isinstance(new_func, (classmethod, staticmethod)):
        new_code = new_func.__func__.__code__
    else:
        new_code = new_func.__code__

    # Figure out how to put the new code back
    if inspect.ismethod(func):
        try:
            # classmethod, staticmethod
            real_func = func.__func__
        except AttributeError:
            real_func = func.im_func
        real_func.__code__ = new_code
        real_func._patchy_the_source = new_source
    else:
        func.__code__ = new_code
        func._patchy_the_source = new_source
