# -*- coding: utf-8 -*-

__author__ = 'Adam Johnson'
__email__ = 'me@adamj.eu'
__version__ = '1.0.0'


import inspect
from textwrap import dedent

import six
from diff_match_patch import diff_match_patch as DMP


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
    patcher = DMP()
    patches = patcher.patch_fromText(patch)
    source, didapply = patcher.patch_apply(patches, source)

    for i, v in enumerate(didapply, 1):
        if not v:
            raise ValueError(
                "Part {} of the patch did not apply"
                .format(i)
            )

    # Recompile
    _set_source(func, source)


def _get_source(func):
    try:
        if inspect.ismethod(func):
            return func.im_func._patchy_the_source
        else:
            return func._patchy_the_source
    except AttributeError:
        source = inspect.getsource(func)
        source = dedent(source)
        return source


def _set_source(func, new_source):
    loc = {}
    six.exec_(new_source, func.func_globals, loc)
    new_func = loc[func.__name__]

    if inspect.ismethod(func):
        func.im_func.func_code = new_func.func_code
        func.im_func._patchy_the_source = new_source
    else:
        func.func_code = new_func.func_code
        func._patchy_the_source = new_source
