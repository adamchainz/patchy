from __future__ import annotations

import sys
from textwrap import dedent
from typing import Callable

import pytest

import patchy.api

if True:
    import __future__


def test_patch():
    def sample() -> int:
        return 1

    assert sample() == 1

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample() -> int:
        -    return 1
        +    return 9001
        """,
    )
    assert sample() == 9001


def test_mc_patchface():
    def sample() -> int:
        return 1

    assert sample() == 1

    patchy.mc_patchface(
        sample,
        """\
        @@ -2,1 +2,1 @@
        -    return 1
        +    return 2
        """,
    )
    assert sample() == 2


def test_patch_simple_no_newline():
    def sample() -> int:
        return 1

    assert sample() == 1

    patchy.patch(
        sample,
        """\
        @@ -2,1 +2,1 @@
        -    return 1
        +    return 2""",
    )
    assert sample() == 2


def test_patch_invalid():
    """
    We need to balk on empty patches
    """

    def sample() -> int:
        return 1

    bad_patch = """garbage
        """
    with pytest.raises(ValueError) as excinfo:
        patchy.patch(sample, bad_patch)

    msg = str(excinfo.value)
    # GNU patch
    expected = dedent(
        """\
        Could not apply the patch to 'sample'. The message from `patch` was:

        patch: **** Only garbage was found in the patch input.

        The code to patch was:
        def sample() -> int:
            return 1

        The patch was:
        garbage
    """
    )
    # BSD patch
    expected2_fragment = "I can't seem to find a patch in there anywhere."
    assert msg == expected or expected2_fragment in msg
    assert sample() == 1


def test_patch_invalid_hunk():
    """
    We need to balk on patches that fail on application
    """

    def sample() -> int:
        return 1

    bad_patch = """\
        @@ -1,2 +1,2 @@
         def sample() -> int:
        -    return 2
        +    return 23"""
    with pytest.raises(ValueError) as excinfo:
        patchy.patch(sample, bad_patch)

    msg = str(excinfo.value)
    assert (
        # GNU patch
        "Hunk #1 FAILED" in msg
        # BSD patch
        or "1 out of 1 hunks failed" in msg
    )
    assert sample() == 1


def test_patch_invalid_hunk_2():
    """
    We need to balk on patches that fail on application
    """

    def sample(x: int) -> int:
        if x == 1:
            print("yes")
        # or
        elif x == 2:
            print("no")
        return 1

    assert sample(1) == 1
    assert sample(2) == 1

    bad_patch = """\
        @@ -1,3 +1,3 @@
         def sample(x: int) -> int:
        -    if x == 1:
        +    if x == 2:
         # or
        @@ -3,3 +3,3 @@
         # or
        -    elif x == 3:
        +    elif x == 4:
                 print("no")
        """
    with pytest.raises(ValueError) as excinfo:
        patchy.patch(sample, bad_patch)

    msg = str(excinfo.value)
    assert (
        # GNU patch
        "Hunk #2 FAILED" in msg
        # BSD patch
        or "1 out of 2 hunks failed" in msg
    )
    assert sample(0) == 1


def test_patch_twice():
    def sample() -> int:
        return 1

    assert sample() == 1

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample() -> int:
        -    return 1
        +    return 2""",
    )
    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample() -> int:
        -    return 2
        +    return 3
        """,
    )

    assert sample() == 3


def test_patch_mutable_default_arg():
    def foo(append: str | None = None, mutable: list[str] = []) -> int:  # noqa: B006
        if append is not None:
            mutable.append(append)
        return len(mutable)

    assert foo() == 0
    assert foo("v1") == 1
    assert foo("v2") == 2
    assert foo(mutable=[]) == 0

    def_line = (
        "def foo(append: str | None = None, mutable: list[str] = [])"
        + " -> int:  # noqa: B006"
    )
    patchy.patch(
        foo,
        f"""\
        @@ -1,2 +1,3 @@
         {def_line}
        +    len(mutable)
             if append is not None:
        """,
    )

    assert foo() == 2
    assert foo("v3") == 3
    assert foo(mutable=[]) == 0


def test_patch_instancemethod():
    class Artist:
        def method(self) -> str:
            return "Chalk"

    assert Artist().method() == "Chalk"

    patchy.patch(
        Artist.method,
        """\
        @@ -1,2 +1,2 @@
         def method(self) -> str:
        -    return "Chalk"
        +    return "Cheese"
        """,
    )

    assert Artist().method() == "Cheese"


def test_patch_instancemethod_freevars():
    def free_func(v: str) -> str:
        return v + " on toast"

    class Artist:
        def method(self) -> str:
            filling = "Chalk"
            return free_func(filling)

    assert Artist().method() == "Chalk on toast"

    patchy.patch(
        Artist.method,
        """\
        @@ -1,3 +1,3 @@
         def method(self) -> str:
        -    filling = "Chalk"
        +    filling = "Cheese"
             return free_func(filling)
        """,
    )

    assert Artist().method() == "Cheese on toast"


def test_patch_init_module_level(tmp_path):
    """
    Module level classes do not have a freevar for their class name, whilst
    classes defined in a scope do...
    """
    example_py = tmp_path / "patch_init_module_level.py"
    example_py.write_text(
        dedent(
            """\
        class Person(object):
            def __init__(self) -> None:
                self.base_prop = 'yo'


        class Artist(Person):
            def __init__(self) -> None:
                super().__init__()
                self.prop = 'old'
    """
        )
    )

    sys.path.insert(0, str(tmp_path))
    try:
        import patch_init_module_level as mod
    finally:
        sys.path.pop(0)
    Artist = mod.Artist

    patchy.patch(
        Artist.__init__,
        """\
        @@ -1,3 +1,3 @@
         def __init__(self) -> None:
             super().__init__()
        -    self.prop = 'old'
        +    self.prop = 'new'
    """,
    )

    a = Artist()
    assert mod.Artist == Artist
    assert a.base_prop == "yo"
    assert a.prop == "new"


def test_patch_recursive_module_level(tmp_path):
    """
    Module level recursive functions do not have a freevar for their name,
    whilst functions defined in a scope do...
    """
    example_py = tmp_path / "patch_recursive_module_level.py"
    example_py.write_text(
        dedent(
            """\
        def factorial(n):
            if n == 1:
                return 1
            else:
                return n * factorial(n-1)
    """
        )
    )
    sys.path.insert(0, str(tmp_path))
    try:
        import patch_recursive_module_level as mod
    finally:
        sys.path.pop(0)
    factorial = mod.factorial

    assert factorial(10) == 3628800

    patchy.patch(
        factorial,
        """\
        @@ -2,4 +2,4 @@
        -    if n == 1:
        -        return 1
        -    else:
        -        return n * factorial(n-1)
        +   if n <= 1:
        +       return n
        +   else:
        +       return factorial(n-1) + factorial(n-2)
    """,
    )

    assert factorial(10) == 55
    assert factorial == mod.factorial


def test_patch_init_super_new():
    class Person:
        def __init__(self) -> None:
            self.base_prop = "yo"

    class Artist(Person):
        def __init__(self) -> None:
            super().__init__()
            self.prop = "old"

    assert Artist().prop == "old"

    patchy.patch(
        Artist.__init__,
        """\
        @@ -1,3 +1,3 @@
         def __init__(self) -> None:
             super().__init__()
        -    self.prop = "old"
        +    self.prop = "new"
        """,
    )

    a = Artist()
    assert a.base_prop == "yo"
    assert a.prop == "new"


def test_patch_freevars():
    def free_func(v: str) -> str:
        return v + " on toast"

    def sample() -> str:
        filling = "Chalk"
        return free_func(filling)

    assert sample() == "Chalk on toast"

    patchy.patch(
        sample,
        """\
        @@ -1,3 +1,3 @@
         def sample() -> str:
        -    filling = "Chalk"
        +    filling = "Cheese"
             return free_func(filling)
        """,
    )

    assert sample() == "Cheese on toast"


def test_patch_freevars_order():
    def tastes_good(v: str) -> str:
        return v + " tastes good"

    def tastes_bad(v: str) -> str:
        return v + " tastes bad"

    def sample() -> str:
        return ", ".join([tastes_good("Cheese"), tastes_bad("Chalk")])

    assert sample() == "Cheese tastes good, Chalk tastes bad"

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample() -> str:
        -    return ", ".join([tastes_good("Cheese"), tastes_bad("Chalk")])
        +    return ", ".join([tastes_bad("Chalk"), tastes_good("Cheese")])
        """,
    )

    assert sample() == "Chalk tastes bad, Cheese tastes good"


def test_patch_freevars_remove():
    def tastes_good(v: str) -> str:
        return v + " tastes good"

    def tastes_bad(v: str) -> str:
        return v + " tastes bad"

    def sample() -> str:
        return ", ".join([tastes_bad("Chalk"), tastes_good("Cheese")])

    assert sample() == "Chalk tastes bad, Cheese tastes good"

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample() -> str:
        -    return ", ".join([tastes_bad("Chalk"), tastes_good("Cheese")])
        +    return ", ".join([tastes_good("Cheese")])
        """,
    )

    assert sample() == "Cheese tastes good"


def test_patch_freevars_nested():
    def free_func(v: str) -> str:
        return v + " on toast"

    def sample() -> Callable[[], str]:
        filling = "Chalk"

        def _inner_func() -> str:
            return free_func(filling)

        return _inner_func

    assert sample()() == "Chalk on toast"

    patchy.patch(
        sample,
        """\
        @@ -1,4 +1,4 @@
         def sample() -> Callable[[], str]:
        -    filling = "Chalk"
        +    filling = "Cheese"

             def _inner_func():
        """,
    )

    assert sample()() == "Cheese on toast"


@pytest.mark.xfail(raises=NameError)
def test_patch_freevars_re_close():
    def nasty_filling() -> str:
        return "Chalk"

    def nice_filling() -> str:
        return "Cheese"

    def sample() -> str:
        filling = nasty_filling()
        return filling + " on toast"

    assert nasty_filling() == "Chalk"
    assert nice_filling() == "Cheese"
    assert sample() == "Chalk on toast"

    patchy.patch(
        sample,
        """\
        @@ -1,3 +1,3 @@
         def sample() -> str:
        -    filling = nasty_filling()
        +    filling = nice_filling()
             return filling + ' on toast'
        """,
    )

    assert sample() == "Cheese on toast"


def test_patch_instancemethod_twice():
    class Artist:
        def method(self) -> str:
            return "Chalk"

    assert Artist().method() == "Chalk"

    patchy.patch(
        Artist.method,
        """\
        @@ -1,2 +1,2 @@
         def method(self) -> str:
        -    return "Chalk"
        +    return "Cheese"
        """,
    )

    patchy.patch(
        Artist.method,
        """\
        @@ -1,2 +1,2 @@
         def method(self) -> str:
        -    return "Cheese"
        +    return "Crackers"
        """,
    )

    assert Artist().method() == "Crackers"


def test_patch_instancemethod_mangled():
    class Artist:
        def __mangled_name(self, v: str) -> str:
            return v + " on toast"

        def method(self) -> str:
            filling = "Chalk"
            return self.__mangled_name(filling)

    assert Artist().method() == "Chalk on toast"

    patchy.patch(
        Artist.method,
        """\
        @@ -1,3 +1,3 @@
         def method(self) -> str:
        -    filling = "Chalk"
        +    filling = "Cheese"
             return self.__mangled_name(filling)
        """,
    )

    assert Artist().method() == "Cheese on toast"


def test_patch_instancemethod_mangled_freevars():
    def _Artist__mangled_name(v: str) -> str:
        return v + " on "

    def plain_name(v: str) -> str:
        return v + "toast"

    class Artist:
        def method(self) -> str:
            filling = "Chalk"
            return plain_name(
                __mangled_name(filling)  # type: ignore [name-defined]  # noqa: F821
            )

    assert Artist().method() == "Chalk on toast"

    patchy.patch(
        Artist.method,
        """\
        @@ -1,3 +1,3 @@
         def method(self) -> str:
        -    filling = "Chalk"
        +    filling = "Cheese"
             return plain_name(__mangled_name(filling))  # noqa: F821
        """,
    )

    assert Artist().method() == "Cheese on toast"


def test_patch_instancemethod_mangled_tabs(tmp_path):
    (tmp_path / "tabs_mangled.py").write_text(
        dedent(
            """\
        class Artist:
        \tdef __mangled_name(self, v: str) -> str:
        \t\treturn v + ' on toast'

        \tdef method(self) -> str:
        \t\tfilling = 'Chalk'
        \t\treturn self.__mangled_name(filling)
    """
        )
    )
    sys.path.insert(0, str(tmp_path))
    try:
        from tabs_mangled import Artist
    finally:
        sys.path.pop(0)

    patchy.patch(
        Artist.method,
        """\
        @@ -1,3 +1,3 @@
         def method(self) -> str:
        -\tfilling = 'Chalk'
        +\tfilling = 'Cheese'
        \treturn __mangled_name(filling)
        """,
    )

    assert Artist().method() == "Cheese on toast"


def test_patch_init():
    class Artist:
        def __init__(self) -> None:
            self.prop = "old"

    assert Artist().prop == "old"

    patchy.patch(
        Artist.__init__,
        """\
        @@ -1,2 +1,2 @@
         def __init__(self) -> None:
        -    self.prop = "old"
        +    self.prop = "new"
        """,
    )

    a = Artist()
    assert a.prop == "new"


def test_patch_init_change_arg():
    class Artist:
        def __init__(self) -> None:
            self.prop = "old"

    assert Artist().prop == "old"

    patchy.patch(
        Artist.__init__,
        """\
        @@ -1,2 +1,2 @@
        -def __init__(self) -> None:
        -    self.prop = "old"
        +def __init__(self, arg: str) -> None:
        +    self.prop = arg
        """,
    )

    a = Artist("new")  # type: ignore [call-arg]
    assert a.prop == "new"


def test_patch_classmethod():
    class Emotion:
        def __init__(self, name: str) -> None:
            self.name = name

        @classmethod
        def create(cls, name: str) -> Emotion:
            return cls(name)

    assert Emotion.create("alright").name == "alright"

    patchy.patch(
        Emotion.create,
        """\
        @@ -1,3 +1,4 @@
         @classmethod
         def create(cls, name: str) -> Emotion:
        +    name = name.title()
             return cls(name)""",
    )

    assert Emotion.create("Happy").name == "Happy"
    assert Emotion.create("happy").name == "Happy"


def test_patch_classmethod_twice():
    class Emotion:
        def __init__(self, name: str) -> None:
            self.name = name

        @classmethod
        def create(cls, name: str) -> Emotion:
            return cls(name)

    assert Emotion.create("alright").name == "alright"

    patchy.patch(
        Emotion.create,
        """\
        @@ -1,3 +1,4 @@
         @classmethod
         def create(cls, name: str) -> Emotion:
        +    name = name.title()
             return cls(name)""",
    )

    patchy.patch(
        Emotion.create,
        """\
        @@ -1,4 +1,4 @@
         @classmethod
         def create(cls, name: str) -> Emotion:
        -    name = name.title()
        +    name = name.lower()
             return cls(name)""",
    )

    assert Emotion.create("happy").name == "happy"
    assert Emotion.create("Happy").name == "happy"
    assert Emotion.create("HAPPY").name == "happy"


def test_patch_staticmethod():
    class Doge:
        @staticmethod
        def bark() -> str:
            return "Woof"

    assert Doge.bark() == "Woof"

    patchy.patch(
        Doge.bark,
        """\
        @@ -1,3 +1,3 @@
         @staticmethod
         def bark() -> str:
        -    return "Woof"
        +    return "Wow\"""",
    )

    assert Doge.bark() == "Wow"


def test_patch_staticmethod_twice():
    class Doge:
        @staticmethod
        def bark() -> str:
            return "Woof"

    assert Doge.bark() == "Woof"

    patchy.patch(
        Doge.bark,
        """\
        @@ -1,3 +1,3 @@
         @staticmethod
         def bark() -> str:
        -    return "Woof"
        +    return "Wow\"""",
    )

    patchy.patch(
        Doge.bark,
        """\
        @@ -1,3 +1,3 @@
         @staticmethod
         def bark() -> str:
        -    return "Wow"
        +    return "Wowowow\"""",
    )

    assert Doge.bark() == "Wowowow"


def test_patch_future_python(tmp_path):
    (tmp_path / "future_user.py").write_text(
        dedent(
            """\
        from __future__ import annotations


        def sample() -> None:
            pass
    """
        )
    )
    sys.path.insert(0, str(tmp_path))
    try:
        from future_user import sample
    finally:
        sys.path.pop(0)

    assert sample.__code__.co_flags & __future__.annotations.compiler_flag

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,3 @@
         def sample() -> None:
        +    pass
             pass
        """,
    )

    assert sample.__code__.co_flags & __future__.annotations.compiler_flag


def test_patch_future_instancemethod(tmp_path):
    (tmp_path / "future_instancemethod.py").write_text(
        dedent(
            """\
        from __future__ import annotations

        class Sample:
            def meth(self) -> None:
                pass
    """
        )
    )
    sys.path.insert(0, str(tmp_path))
    try:
        from future_instancemethod import Sample
    finally:
        sys.path.pop(0)

    assert Sample.meth.__code__.co_flags & __future__.annotations.compiler_flag

    patchy.patch(
        Sample.meth,
        """\
        @@ -1,2 +1,3 @@
         def meth(self) -> None:
        +    pass
             pass
        """,
    )

    assert Sample.meth.__code__.co_flags & __future__.annotations.compiler_flag


def test_patch_nonlocal_fails():
    variab = 20

    def get_function() -> Callable[[], int]:
        variab = 15

        def sample() -> int:
            nonlocal variab
            multiple = 3
            return variab * multiple

        return sample

    sample = get_function()

    assert sample() == 15 * 3

    patchy.patch(
        sample,
        """\
        @@ -2,3 +2,3 @@
             nonlocal variab
        -    multiple = 3
        +    multiple = 4
        """,
    )

    assert sample() == 15 * 4


def test_patch_by_path(tmp_path):
    package = tmp_path / "patch_by_path_pkg"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "mod.py").write_text(
        dedent(
            """\
        class Foo:
            def sample(self) -> int:
                return 1
        """
        )
    )
    sys.path.insert(0, str(tmp_path))
    try:
        patchy.patch(
            "patch_by_path_pkg.mod.Foo.sample",
            """\
            @@ -2,1 +2,1 @@
            -    return 1
            +    return 2
            """,
        )
        from patch_by_path_pkg.mod import Foo
    finally:
        sys.path.pop(0)

    assert Foo().sample() == 2


def test_patch_by_path_already_imported(tmp_path):
    package = tmp_path / "patch_by_path_pkg2"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "mod.py").write_text(
        dedent(
            """\
        class Foo:
            def sample(self) -> int:
                return 1
        """
        )
    )
    sys.path.insert(0, str(tmp_path))
    try:
        from patch_by_path_pkg2.mod import Foo

        assert Foo().sample() == 1
        patchy.patch(
            "patch_by_path_pkg2.mod.Foo.sample",
            """\
            @@ -2,1 +2,1 @@
            -    return 1
            +    return 2
            """,
        )
    finally:
        sys.path.pop(0)

    assert Foo().sample() == 2
