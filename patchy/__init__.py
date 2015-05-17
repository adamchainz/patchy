# -*- coding: utf-8 -*-

__author__ = 'Adam Johnson'
__email__ = 'me@adamj.eu'
__version__ = '1.0.0'


import inspect
from textwrap import dedent

import six
import whatthepatch


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
    patch = dedent(patch).lstrip()

    source = _get_source(func)

    # Diff
    diffs = [x for x in whatthepatch.parse_patch(patch)]
    if not len(diffs):
        raise ValueError("Invalid patch.")

    for i, diff in enumerate(diffs, 1):
        try:
            source = '\n'.join(whatthepatch.apply_diff(diff, source))
        except AssertionError:
            raise ValueError(
                "Hunk {num} of the patch was invalid - could not apply:\n\n"
                "{patch}\n"
                "to source:\n\n"
                "{source}"
                .format(num=i, patch=patch, source=source)
            )

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
