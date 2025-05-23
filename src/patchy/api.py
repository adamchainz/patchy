from __future__ import annotations

import ast
import inspect
import os
import shutil
import subprocess
from functools import wraps
from tempfile import mkdtemp
from textwrap import dedent
from types import CodeType, TracebackType
from typing import Any, Callable, TypeVar, cast
from weakref import WeakKeyDictionary

from .cache import PatchingCache

if True:
    import __future__

from pkgutil import resolve_name as pkgutil_resolve_name

__all__ = ("patch", "mc_patchface", "unpatch", "replace", "temp_patch")


# Public API


def patch(func: Callable[..., Any] | str, patch_text: str) -> None:
    _do_patch(func, patch_text, forwards=True)


mc_patchface = patch


def unpatch(func: Callable[..., Any] | str, patch_text: str) -> None:
    _do_patch(func, patch_text, forwards=False)


def replace(
    func: Callable[..., Any],
    expected_source: str | None,
    new_source: str,
) -> None:
    if expected_source is not None:
        expected_source = dedent(expected_source)
        current_source = _get_source(func)
        _assert_ast_equal(current_source, expected_source, func.__name__)

    new_source = dedent(new_source)
    _set_source(func, new_source)


AnyFunc = TypeVar("AnyFunc", bound=Callable[..., Any])


class temp_patch:
    def __init__(self, func: Callable[..., Any] | str, patch_text: str) -> None:
        self.func = func
        self.patch_text = patch_text

    def __enter__(self) -> None:
        patch(self.func, self.patch_text)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        unpatch(self.func, self.patch_text)

    def __call__(self, decorable: AnyFunc) -> AnyFunc:
        @wraps(decorable)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self:
                decorable(*args, **kwargs)

        return cast(AnyFunc, wrapper)


# Gritty internals


def _do_patch(
    func: Callable[..., Any] | str,
    patch_text: str,
    forwards: bool,
) -> None:
    if isinstance(func, str):
        func = cast(Callable[..., Any], pkgutil_resolve_name(func))
    source = _get_source(func)
    patch_text = dedent(patch_text)

    new_source = _apply_patch(source, patch_text, forwards, func.__name__)

    _set_source(func, new_source)


_patching_cache = PatchingCache(maxsize=100)


def _apply_patch(
    source: str,
    patch_text: str,
    forwards: bool,
    name: str,
) -> str:
    # Cached ?
    try:
        return _patching_cache.retrieve(source, patch_text, forwards)
    except KeyError:
        pass

    # Write out files
    tempdir = mkdtemp(prefix="patchy")
    try:
        source_path = os.path.join(tempdir, name + ".py")
        with open(source_path, "w") as source_file:
            source_file.write(source)

        patch_path = os.path.join(tempdir, name + ".patch")
        with open(patch_path, "w") as patch_file:
            patch_file.write(patch_text)
            if not patch_text.endswith("\n"):
                patch_file.write("\n")

        # Call `patch` command
        command = ["patch", "--force"]
        if not forwards:
            command.append("--reverse")
        command.extend([source_path, patch_path])
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            msg = "Could not {action} the patch {prep} '{name}'.".format(
                action=("apply" if forwards else "unapply"),
                prep=("to" if forwards else "from"),
                name=name,
            )
            msg += f" The message from `patch` was:\n{result.stdout}\n{result.stderr}"
            msg += f"\nThe code to patch was:\n{source}\nThe patch was:\n{patch_text}"
            raise ValueError(msg)

        with open(source_path) as source_file:
            new_source = source_file.read()
    finally:
        shutil.rmtree(tempdir)

    _patching_cache.store(source, patch_text, forwards, new_source)

    return new_source


def _get_flags_mask() -> int:
    result = 0
    for name in __future__.all_feature_names:
        result |= getattr(__future__, name).compiler_flag
    return result


FEATURE_MASK = _get_flags_mask()


# Stores the source of functions that have had their source changed
_source_map: WeakKeyDictionary[Callable[..., Any], str] = WeakKeyDictionary()


def _get_source(func: Callable[..., Any]) -> str:
    real_func = _get_real_func(func)
    try:
        return _source_map[real_func]
    except KeyError:
        source = inspect.getsource(func)
        source = dedent(source)
        return source


def _class_name(func: Callable[..., Any]) -> str | None:
    split_name = func.__qualname__.split(".")
    try:
        class_name = split_name[-2]
    except IndexError:
        return None
    else:
        if class_name == "<locals>":
            return None
        return class_name


def _set_source(func: Callable[..., Any], func_source: str) -> None:
    # Fetch the actual function we are changing
    real_func = _get_real_func(func)
    # Figure out any future headers that may be required
    feature_flags = real_func.__code__.co_flags & FEATURE_MASK

    class_name = _class_name(func)

    def _compile(
        code: str | ast.Module,
        flags: int = 0,
    ) -> CodeType | ast.Module:
        result: CodeType | ast.Module = compile(
            code, "<patchy>", "exec", flags=feature_flags | flags, dont_inherit=True
        )
        return result

    def _parse(code: str) -> ast.Module:
        result = _compile(code, flags=ast.PyCF_ONLY_AST)
        assert isinstance(result, ast.Module)
        return result

    def _process_freevars() -> tuple[str, ast.AST, list[str]]:
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
        _def = "def __patchy_freevars__():"
        fvs = func.__code__.co_freevars
        fv_body = [f"    {fv} = object()" for fv in fvs]
        fv_force_use_body = [f"    {fv}" for fv in fvs]
        if fv_force_use_body:
            fv_force_use_ast = _parse("\n".join([_def] + fv_force_use_body))
            fv_force_use = fv_force_use_ast.body[0].body  # type: ignore [attr-defined]
        else:
            fv_force_use = []
        _ast = _parse(func_source).body[0]
        _ast.body = _ast.body + fv_force_use  # type: ignore [attr-defined]
        return _def, _ast, fv_body

    def _process_method() -> ast.Module:
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
        _global = (
            ""
            if class_name in func.__code__.co_freevars
            else f"    global {class_name}\n"
        )
        class_src = f"{_global}    class {class_name}(object):\n        pass"
        ret = f"    return {class_name}.{func.__name__}"
        to_parse = "\n".join([_def] + fv_body + [class_src, ret])
        new_source = _parse(to_parse)
        new_source.body[0].body[-2].body[0] = _ast  # type: ignore [attr-defined]
        return new_source

    def _process_function() -> ast.Module:
        _def, _ast, fv_body = _process_freevars()
        name = func.__name__
        ret = f"    return {name}"
        _global = [] if name in func.__code__.co_freevars else [f"    global {name}"]
        to_parse = "\n".join([_def] + _global + fv_body + ["    pass", ret])
        new_source = _parse(to_parse)
        new_source.body[0].body[-2] = _ast  # type: ignore [attr-defined]
        return new_source

    if class_name:
        new_source = _process_method()
    else:
        new_source = _process_function()

    # Compile and retrieve the new Code object
    localz: dict[str, Any] = {}
    new_code = cast(CodeType, _compile(new_source))

    exec(
        new_code,
        dict(func.__globals__),
        localz,
    )
    new_func = localz["__patchy_freevars__"]()

    # Put the new Code object in place
    real_func.__code__ = new_func.__code__
    # Store the modified source. This used to be attached to the function but
    # that is a bit naughty
    _source_map[real_func] = func_source


def _get_real_func(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Duplicates some of the logic implicit in inspect.getsource(). Basically
    some function-esque things, such as classmethods, aren't functions but we
    can peel back the layers to the underlying function very easily.
    """
    if inspect.ismethod(func):
        return func.__func__
    else:
        return func


def _assert_ast_equal(current_source: str, expected_source: str, name: str) -> None:
    current_ast = ast.parse(current_source)
    expected_ast = ast.parse(expected_source)
    if ast.dump(current_ast) != ast.dump(expected_ast):
        msg = (
            f"The code of '{name}' has changed from expected.\n"
            f"The current code is:\n{current_source}\n"
            f"The expected code is:\n{expected_source}"
        )
        raise ValueError(msg)
