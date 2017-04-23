# -*- encoding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import ast
import inspect
from functools import wraps
from textwrap import dedent
from weakref import WeakKeyDictionary

import six
import whatthepatch

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

    diff = list(whatthepatch.parse_patch(patch_text))

    if len(diff) != 1:
        raise ValueError('Invalid patch')

    new_source = '\n'.join(whatthepatch.apply_diff(
        diff[0],
        source,
        reverse=not forwards,
    ))

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

    class_name = _class_name(func)

    def _compile(code, flags=0):
        return compile(
            code,
            '<patchy>',
            'exec',
            flags=feature_flags | flags,
            dont_inherit=True,
        )

    def _parse(code):
        return _compile(code, flags=ast.PyCF_ONLY_AST)

    def _process_freevars():
        """
        Wrap the new function in a __patchy_freevars__ method that provides all
        freevars of the original function.

        Because the new function must use exectaly the same freevars as the
        original, also append to the new function with a body of code to force
        use of those freevars (in the case the the patch drops use of any
        freevars):

        def __patchy_freevars__():
            eg_free_var_spam = object()  <- added in wrapper
            eg_free_var_ham = object()   <- added in wrapper

            def patched_func():
                return some_global(eg_free_var_ham)
                eg_free_var_spam         <- appended to new func body
                eg_free_var_ham          <- appended to new func body

            return patched_func
        """
        _def = 'def __patchy_freevars__():'
        fvs = func.__code__.co_freevars
        fv_body = ['    {0} = object()'.format(fv) for fv in fvs]
        fv_force_use_body = ['    {0}'.format(fv) for fv in fvs]
        if fv_force_use_body:
            fv_force_use_ast = _parse('\n'.join([_def] + fv_force_use_body))
            fv_force_use = fv_force_use_ast.body[0].body
        else:
            fv_force_use = []
        _ast = _parse(func_source).body[0]
        _ast.body = _ast.body + fv_force_use
        return _def, _ast, fv_body

    def _process_method():
        """
        Wrap the new method in a class to ensure the same mangling as would
        have been performed on the original method:

        def __patchy_freevars__():

            class SomeClass(object):
                def patched_func(self):
                    return some_globals(self.__some_mangled_prop)

            return SomeClass.patched_func
        """

        _def, _ast, fv_body = _process_freevars()
        class_src = '    class {name}(object):\n        pass'.format(name=class_name)
        ret = '    return {class_name}.{name}'.format(
            class_name=class_name,
            name=func.__name__,
        )
        to_parse = '\n'.join([_def] + fv_body + [class_src, ret])
        new_source = _parse(to_parse)
        new_source.body[0].body[-2].body[0] = _ast
        return new_source

    def _process_function():
        _def, _ast, fv_body = _process_freevars()
        ret = '    return {name}'.format(name=func.__name__)
        to_parse = '\n'.join([_def] + fv_body + ['    pass', ret])
        new_source = _parse(to_parse)
        new_source.body[0].body[-2] = _ast
        return new_source

    if class_name:
        new_source = _process_method()
    else:
        new_source = _process_function()

    # Compile and retrieve the new Code object
    localz = {}
    new_code = _compile(new_source)

    six.exec_(new_code, func.__globals__, localz)
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
