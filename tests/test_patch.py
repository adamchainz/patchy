import __future__

import sys
from textwrap import dedent

import pytest
import six

import patchy
import patchy.api


def test_patch():
    def sample():
        return 1

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return 1
        +    return 9001
        """,
    )
    assert sample() == 9001


def test_mc_patchface():
    def sample():
        return 1

    patchy.mc_patchface(
        sample,
        """\
        @@ -2,2 +2,2 @@
        -    return 1
        +    return 2
        """,
    )
    assert sample() == 2


def test_patch_simple_no_newline():
    def sample():
        return 1

    patchy.patch(
        sample,
        """\
        @@ -2,2 +2,2 @@
        -    return 1
        +    return 2""",
    )
    assert sample() == 2


def test_patch_invalid():
    """
    We need to balk on empty patches
    """

    def sample():
        return 1

    bad_patch = """garbage
        """
    with pytest.raises(ValueError) as excinfo:
        patchy.patch(sample, bad_patch)

    msg = str(excinfo.value)
    expected = dedent(
        """\
        Could not apply the patch to 'sample'. The message from `patch` was:

        patch: **** Only garbage was found in the patch input.

        The code to patch was:
        def sample():
            return 1

        The patch was:
        garbage
    """
    )
    assert msg == expected
    assert sample() == 1


def test_patch_invalid_hunk():
    """
    We need to balk on patches that fail on application
    """

    def sample():
        return 1

    bad_patch = """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return 2
        +    return 23"""
    with pytest.raises(ValueError) as excinfo:
        patchy.patch(sample, bad_patch)

    assert "Hunk #1 FAILED" in str(excinfo.value)
    assert sample() == 1


def test_patch_invalid_hunk_2():
    """
    We need to balk on patches that fail on application
    """

    def sample():
        if True:
            print("yes")
        if False:
            print("no")
        return 1

    bad_patch = """\
        @@ -1,2 +1,2 @@
         def sample():
        -    if True:
        +    if False:
        @@ -3,5 +3,5 @@
                 print("yes")
        -    if Falsy:
        +    if Truey:
                 print("no")
        """
    with pytest.raises(ValueError) as excinfo:
        patchy.patch(sample, bad_patch)

    assert "Hunk #2 FAILED" in str(excinfo.value)
    assert sample() == 1


def test_patch_twice():
    def sample():
        return 1

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return 1
        +    return 2""",
    )
    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return 2
        +    return 3
        """,
    )

    assert sample() == 3


def test_patch_mutable_default_arg():
    def foo(append=None, mutable=[]):  # noqa: B006
        if append is not None:
            mutable.append(append)
        return len(mutable)

    assert foo() == 0
    assert foo("v1") == 1
    assert foo("v2") == 2
    assert foo(mutable=[]) == 0

    patchy.patch(
        foo,
        """\
        @@ -1,2 +1,3 @@
         def foo(append=None, mutable=[]):
        +    len(mutable)
             if append is not None:
        """,
    )

    assert foo() == 2
    assert foo("v3") == 3
    assert foo(mutable=[]) == 0


def test_patch_instancemethod():
    class Artist(object):
        def method(self):
            return "Chalk"

    patchy.patch(
        Artist.method,
        """\
        @@ -1,2 +1,2 @@
         def method(self):
        -    return "Chalk"
        +    return "Cheese"
        """,
    )

    assert Artist().method() == "Cheese"


def test_patch_instancemethod_freevars():
    def free_func(v):
        return v + " on toast"

    class Artist:
        def method(self):
            filling = "Chalk"
            return free_func(filling)

    patchy.patch(
        Artist.method,
        """\
        @@ -1,2 +1,2 @@
         def method(self):
        -    filling = "Chalk"
        +    filling = "Cheese"
             return free_func(filling)
        """,
    )

    assert Artist().method() == "Cheese on toast"


def test_patch_init_module_level(tmpdir):
    """
    Module level classes do not have a freevar for their class name, whilst
    classes defined in a scope do...
    """
    example_py = tmpdir.join("patch_init_module_level.py")
    example_py.write(
        dedent(
            """\
        class Person(object):
            def __init__(self):
                self.base_prop = 'yo'


        class Artist(Person):
            def __init__(self):
                super(Artist, self).__init__()
                self.prop = 'old'
    """
        )
    )
    mod = example_py.pyimport()
    Artist = mod.Artist

    patchy.patch(
        Artist.__init__,
        """\
        @@ -1,3 +1,3 @@
         def __init__(self):
             super(Artist, self).__init__()
        -    self.prop = 'old'
        +    self.prop = 'new'
    """,
    )

    a = Artist()
    assert mod.Artist == Artist
    assert a.base_prop == "yo"
    assert a.prop == "new"


def test_patch_recursive_module_level(tmpdir):
    """
    Module level recursive functions do not have a freevar for their name,
    whilst functions defined in a scope do...
    """
    example_py = tmpdir.join("patch_recursive_module_level.py")
    example_py.write(
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
    mod = example_py.pyimport()
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
    class Person(object):
        def __init__(self):
            self.base_prop = "yo"

    class Artist(Person):
        def __init__(self):
            super().__init__()
            self.prop = "old"

    patchy.patch(
        Artist.__init__,
        """\
        @@ -1,3 +1,3 @@
         def __init__(self):
             super().__init__()
        -    self.prop = "old"
        +    self.prop = "new"
        """,
    )

    a = Artist()
    assert a.base_prop == "yo"
    assert a.prop == "new"


def test_patch_freevars():
    def free_func(v):
        return v + " on toast"

    def sample():
        filling = "Chalk"
        return free_func(filling)

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def method():
        -    filling = "Chalk"
        +    filling = "Cheese"
             return free_func(filling)
        """,
    )

    assert sample() == "Cheese on toast"


def test_patch_freevars_order():
    def tastes_good(v):
        return v + " tastes good"

    def tastes_bad(v):
        return v + " tastes bad"

    def sample():
        return ", ".join([tastes_good("Cheese"), tastes_bad("Chalk")])

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return ", ".join([tastes_good("Cheese"), tastes_bad("Chalk")])
        +    return ", ".join([tastes_bad("Chalk"), tastes_good("Cheese")])
        """,
    )

    assert sample() == "Chalk tastes bad, Cheese tastes good"


def test_patch_freevars_remove():
    def tastes_good(v):
        return v + " tastes good"

    def tastes_bad(v):
        return v + " tastes bad"

    def sample():
        return ", ".join([tastes_bad("Chalk"), tastes_good("Cheese")])

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return ", ".join([tastes_bad("Chalk"), tastes_good("Cheese")])
        +    return ", ".join([tastes_good("Cheese")])
        """,
    )

    assert sample() == "Cheese tastes good"


def test_patch_freevars_nested():
    def free_func(v):
        return v + " on toast"

    def sample():
        filling = "Chalk"

        def _inner_func():
            return free_func(filling)

        return _inner_func

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample():
        -    filling = "Chalk"
        +    filling = "Cheese"

             def _inner_func():
        """,
    )

    assert sample()() == "Cheese on toast"


@pytest.mark.xfail(raises=NameError)
def test_patch_freevars_re_close():
    def nasty_filling(v):
        return "Chalk"

    def nice_filling(v):
        return "Cheese"

    def sample():
        filling = nasty_filling()
        return filling + " on toast"

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample():
        -    filling = nasty_filling()
        +    filling = nice_filling()
             return filling + ' on toast'
        """,
    )

    assert sample() == "Cheese on toast"


def test_patch_instancemethod_twice():
    class Artist(object):
        def method(self):
            return "Chalk"

    patchy.patch(
        Artist.method,
        """\
        @@ -1,2 +1,2 @@
         def method(self):
        -    return "Chalk"
        +    return "Cheese"
        """,
    )

    patchy.patch(
        Artist.method,
        """\
        @@ -1,2 +1,2 @@
         def method(self):
        -    return "Cheese"
        +    return "Crackers"
        """,
    )

    assert Artist().method() == "Crackers"


def test_patch_instancemethod_mangled():
    class Artist(object):
        def __mangled_name(self, v):
            return v + " on toast"

        def method(self):
            filling = "Chalk"
            return self.__mangled_name(filling)

    patchy.patch(
        Artist.method,
        """\
        @@ -1,2 +1,2 @@
         def method(self):
        -    filling = "Chalk"
        +    filling = "Cheese"
             return self.__mangled_name(filling)
        """,
    )

    assert Artist().method() == "Cheese on toast"


def test_patch_old_class_instancemethod_mangled():
    class Artist:
        def __mangled_name(self, v):
            return v + " on toast"

        def method(self):
            filling = "Chalk"
            return self.__mangled_name(filling)

    patchy.patch(
        Artist.method,
        """\
        @@ -1,2 +1,2 @@
         def method(self):
        -    filling = "Chalk"
        +    filling = "Cheese"
             return self.__mangled_name(filling)
        """,
    )

    assert Artist().method() == "Cheese on toast"


def test_patch_instancemethod_mangled_freevars():
    def _Artist__mangled_name(v):
        return v + " on "

    def plain_name(v):
        return v + "toast"

    class Artist:
        def method(self):
            filling = "Chalk"
            return plain_name(__mangled_name(filling))  # noqa: F821

    patchy.patch(
        Artist.method,
        """\
        @@ -1,2 +1,2 @@
         def method(self):
        -    filling = "Chalk"
        +    filling = "Cheese"
             return plain_name(__mangled_name(filling))  # noqa: F821
        """,
    )

    assert Artist().method() == "Cheese on toast"


def test_patch_instancemethod_mangled_tabs(tmpdir):
    tmpdir.join("tabs_mangled.py").write(
        dedent(
            """\
        class Artist:
        \tdef __mangled_name(self, v):
        \t\treturn v + ' on toast'

        \tdef method(self):
        \t\tfilling = 'Chalk'
        \t\treturn self.__mangled_name(filling)
    """
        )
    )
    sys.path.insert(0, six.text_type(tmpdir))

    try:
        from tabs_mangled import Artist
    finally:
        sys.path.pop(0)

    patchy.patch(
        Artist.method,
        """\
        @@ -1,2 +1,2 @@
         def method(self):
        -\tfilling = 'Chalk'
        +\tfilling = 'Cheese'
        \treturn __mangled_name(filling)
        """,
    )

    assert Artist().method() == "Cheese on toast"


def test_patch_init():
    class Artist(object):
        def __init__(self):
            self.prop = "old"

    patchy.patch(
        Artist.__init__,
        """\
        @@ -1,2 +1,2 @@
         def __init__(self):
        -    self.prop = "old"
        +    self.prop = "new"
        """,
    )

    a = Artist()
    assert a.prop == "new"


def test_patch_init_change_arg():
    class Artist(object):
        def __init__(self):
            self.prop = "old"

    patchy.patch(
        Artist.__init__,
        """\
        @@ -1,2 +1,2 @@
        -def __init__(self):
        -    self.prop = "old"
        +def __init__(self, arg):
        +    self.prop = arg
        """,
    )

    a = Artist("new")
    assert a.prop == "new"


def test_patch_classmethod():
    class Emotion(object):
        def __init__(self, name):
            self.name = name

        @classmethod
        def create(cls, name):
            return cls(name)

    patchy.patch(
        Emotion.create,
        """\
        @@ -1,2 +1,3 @@
         @classmethod
         def create(cls, name):
        +    name = name.title()
             return cls(name)""",
    )

    assert Emotion.create("Happy").name == "Happy"
    assert Emotion.create("happy").name == "Happy"


def test_patch_classmethod_twice():
    class Emotion(object):
        def __init__(self, name):
            self.name = name

        @classmethod
        def create(cls, name):
            return cls(name)

    patchy.patch(
        Emotion.create,
        """\
        @@ -1,2 +1,3 @@
         @classmethod
         def create(cls, name):
        +    name = name.title()
             return cls(name)""",
    )

    patchy.patch(
        Emotion.create,
        """\
        @@ -1,3 +1,3 @@
         @classmethod
         def create(cls, name):
        -    name = name.title()
        +    name = name.lower()
             return cls(name)""",
    )

    assert Emotion.create("happy").name == "happy"
    assert Emotion.create("Happy").name == "happy"
    assert Emotion.create("HAPPY").name == "happy"


def test_patch_staticmethod():
    class Doge(object):
        @staticmethod
        def bark():
            return "Woof"

    patchy.patch(
        Doge.bark,
        """\
        @@ -1,3 +1,3 @@
         @staticmethod
         def bark():
        -    return "Woof"
        +    return "Wow\"""",
    )

    assert Doge.bark() == "Wow"


def test_patch_staticmethod_twice():
    class Doge(object):
        @staticmethod
        def bark():
            return "Woof"

    patchy.patch(
        Doge.bark,
        """\
        @@ -1,3 +1,3 @@
         @staticmethod
         def bark():
        -    return "Woof"
        +    return "Wow\"""",
    )

    patchy.patch(
        Doge.bark,
        """\
        @@ -1,3 +1,3 @@
         @staticmethod
         def bark():
        -    return "Wow"
        +    return "Wowowow\"""",
    )

    assert Doge.bark() == "Wowowow"


@pytest.mark.skipif(
    sys.version_info >= (3, 7), reason="generator_stop made mandatory in Python 3.7"
)
def test_patch_future_python_3_5_to_3_7(tmpdir):
    tmpdir.join("future_user.py").write(
        dedent(
            """\
        from __future__ import generator_stop

        def f(x):
            raise StopIteration()


        def sample():
            return list(f(x) for x in range(10))
    """
        )
    )
    sys.path.insert(0, six.text_type(tmpdir))

    try:
        from future_user import sample
    finally:
        sys.path.pop(0)

    with pytest.raises(RuntimeError):
        sample()

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,3 @@
         def sample():
        +    pass
             return list(f(x) for x in range(10))
        """,
    )

    with pytest.raises(RuntimeError):
        sample()


@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="__future__.annotations introduced in Python 3.7"
)
def test_patch_future_python_3_7_plus(tmpdir):
    tmpdir.join("future_user.py").write(
        dedent(
            """\
        from __future__ import annotations


        def sample():
            pass
    """
        )
    )
    sys.path.insert(0, six.text_type(tmpdir))

    try:
        from future_user import sample
    finally:
        sys.path.pop(0)

    assert sample.__code__.co_flags & __future__.annotations.compiler_flag

    patchy.patch(
        sample,
        """\
        @@ -1,2 +1,3 @@
         def sample():
        +    pass
             pass
        """,
    )

    assert sample.__code__.co_flags & __future__.annotations.compiler_flag


@pytest.mark.skipif(
    sys.version_info >= (3, 7), reason="generator_stop made mandatory in Python 3.7"
)
def test_patch_future_instancemethod_python_3_5_to_3_7(tmpdir):
    tmpdir.join("future_instancemethod.py").write(
        dedent(
            """\
        from __future__ import generator_stop

        def f(x):
            raise StopIteration()

        class Sample(object):
            def meth(self):
                return list(f(x) for x in range(10))
    """
        )
    )
    sys.path.insert(0, six.text_type(tmpdir))

    try:
        from future_instancemethod import Sample
    finally:
        sys.path.pop(0)

    with pytest.raises(RuntimeError):
        Sample().meth()

    patchy.patch(
        Sample.meth,
        """\
        @@ -1,2 +1,3 @@
         def meth(self):
        +    pass
             return list(f(x) for x in range(10))
        """,
    )

    with pytest.raises(RuntimeError):
        Sample().meth()


@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="__future__.annotations introduced in Python 3.7"
)
def test_patch_future_instancemethod_python_3_7_plus(tmpdir):
    tmpdir.join("future_instancemethod.py").write(
        dedent(
            """\
        from __future__ import annotations

        class Sample(object):
            def meth(self):
                pass
    """
        )
    )
    sys.path.insert(0, six.text_type(tmpdir))

    try:
        from future_instancemethod import Sample
    finally:
        sys.path.pop(0)

    assert Sample.meth.__code__.co_flags & __future__.annotations.compiler_flag

    patchy.patch(
        Sample.meth,
        """\
        @@ -1,2 +1,3 @@
         def meth(self):
        +    pass
             pass
        """,
    )

    assert Sample.meth.__code__.co_flags & __future__.annotations.compiler_flag


def test_patch_nonlocal_fails(tmpdir):
    # Put in separate file since it would SyntaxError on Python 2
    tmpdir.join("py3_nonlocal.py").write(
        dedent(
            """\
        variab = 20


        def get_function():
            variab = 15

            def sample():
                nonlocal variab
                multiple = 3
                return variab * multiple

            return sample

        sample = get_function()
    """
        )
    )
    sys.path.insert(0, six.text_type(tmpdir))
    try:
        from py3_nonlocal import sample
    finally:
        sys.path.pop(0)

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


def test_patch_by_path(tmpdir):
    package = tmpdir.mkdir("patch_by_path_pkg")
    package.join("__init__.py").ensure(file=True)
    package.join("mod.py").write(
        dedent(
            """\
        class Foo(object):
            def sample(self):
                return 1
        """
        )
    )
    sys.path.insert(0, six.text_type(tmpdir))
    try:
        patchy.patch(
            "patch_by_path_pkg.mod.Foo.sample",
            """\
            @@ -2,2 +2,2 @@
            -    return 1
            +    return 2
            """,
        )
        from patch_by_path_pkg.mod import Foo
    finally:
        sys.path.pop(0)

    assert Foo().sample() == 2


def test_patch_by_path_already_imported(tmpdir):
    package = tmpdir.mkdir("patch_by_path_pkg2")
    package.join("__init__.py").ensure(file=True)
    package.join("mod.py").write(
        dedent(
            """\
        class Foo(object):
            def sample(self):
                return 1
        """
        )
    )
    sys.path.insert(0, six.text_type(tmpdir))
    try:
        from patch_by_path_pkg2.mod import Foo

        assert Foo().sample() == 1
        patchy.patch(
            "patch_by_path_pkg2.mod.Foo.sample",
            """\
            @@ -2,2 +2,2 @@
            -    return 1
            +    return 2
            """,
        )
    finally:
        sys.path.pop(0)

    assert Foo().sample() == 2
