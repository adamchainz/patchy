# -*- coding: utf-8 -*-

__author__ = 'Adam Johnson'
__email__ = 'me@adamj.eu'
__version__ = '1.0.0'


import inspect
import subprocess
import tempfile
import os
import shutil
from textwrap import dedent

import six


def replace(func, find, replace, count=None):
    # Get the raw source code
    source = _get_source(func)

    if source.find(find) == -1:
        raise ValueError("{} not found in the source".format(find))

    if count is not None:
        num = source.count(find)
        if num != count:
            raise ValueError("{} occurences of '{}' expected, {} found."
                             .format(count, find, num))

    source = source.replace(find, replace)

    # Recompile
    _set_source(func, source)


def patch(func, patch):
    source = _get_source(func)
    patch = dedent(patch)

    # Write out files
    tempdir = tempfile.mkdtemp(prefix='patchy')
    try:
        source_path = os.path.join(tempdir, func.__name__ + '.py')
        with open(source_path, 'w') as source_file:
            source_file.write(source)

        patch_path = os.path.join(tempdir, func.__name__ + '.patch')
        with open(patch_path, 'w') as patch_file:
            patch_file.write(patch)
            if not patch.endswith('\n'):
                patch_file.write('\n')

        # Call `patch` command
        proc = subprocess.Popen(
            ['patch', source_path, patch_path],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        stdout, stderr = proc.communicate()

        if proc.returncode != 0:
            msg = "Could not apply the patch to '{}'.".format(func.__name__)
            if stdout or stderr:
                msg += " The message from `patch` was:\n{}\n{}".format(
                    stdout.decode('utf-8'),
                    stderr.decode('utf-8')
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
