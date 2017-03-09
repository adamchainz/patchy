# -*- encoding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import unittest
from textwrap import dedent

import pytest
import six

import patchy
import patchy.api

from .base import PatchyTestCase


class TestPatch(PatchyTestCase):

    def test_patch(self):
        def sample():
            return 1

        patchy.patch(sample, """\
            @@ -1,2 +1,2 @@
             def sample():
            -    return 1
            +    return 9001
            """)
        assert sample() == 9001

    def test_mc_patchface(self):
        def sample():
            return 1

        patchy.mc_patchface(sample, """\
            @@ -2,2 +2,2 @@
            -    return 1
            +    return 2
            """)
        assert sample() == 2

    def test_patch_simple_no_newline(self):
        def sample():
            return 1

        patchy.patch(sample, """\
            @@ -2,2 +2,2 @@
            -    return 1
            +    return 2""")
        assert sample() == 2

    def test_patch_invalid(self):
        """
        We need to balk on empty patches
        """
        def sample():
            return 1

        bad_patch = """
            """
        with pytest.raises(ValueError) as excinfo:
            patchy.patch(sample, bad_patch)

        msg = str(excinfo.value)
        assert msg.startswith("Could not apply the patch to 'sample'.")
        assert "Only garbage was found in the patch input."
        assert sample() == 1

    def test_patch_invalid_hunk(self):
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

    def test_patch_invalid_hunk_2(self):
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

    def test_patch_twice(self):
        def sample():
            return 1

        patchy.patch(sample, """\
            @@ -1,2 +1,2 @@
             def sample():
            -    return 1
            +    return 2""")
        patchy.patch(sample, """\
            @@ -1,2 +1,2 @@
             def sample():
            -    return 2
            +    return 3
            """)

        assert sample() == 3

    def test_patch_mutable_default_arg(self):
        def foo(append=None, mutable=[]):
            if append is not None:
                mutable.append(append)
            return len(mutable)

        assert foo() == 0
        assert foo('v1') == 1
        assert foo('v2') == 2
        assert foo(mutable=[]) == 0

        patchy.patch(foo, """\
            @@ -1,2 +1,3 @@
             def foo(append=None, mutable=[]):
            +    len(mutable)
                 if append is not None:
            """)

        assert foo() == 2
        assert foo('v3') == 3
        assert foo(mutable=[]) == 0

    def test_patch_instancemethod(self):
        class Artist(object):
            def method(self):
                return 'Chalk'

        patchy.patch(Artist.method, """\
            @@ -1,2 +1,2 @@
             def method(self):
            -    return 'Chalk'
            +    return 'Cheese'
            """)

        assert Artist().method() == "Cheese"

    def test_patch_instancemethod_freevars(self):
        def free_func(v):
            return v + ' on toast'

        class Artist:
            def method(self):
                filling = 'Chalk'
                return free_func(filling)

        patchy.patch(Artist.method, """\
            @@ -1,2 +1,2 @@
             def method(self):
            -    filling = 'Chalk'
            +    filling = 'Cheese'
                 return free_func(filling)
            """)

        assert Artist().method() == "Cheese on toast"

    @unittest.skipUnless(six.PY3, "Python 3 required for PEP 3135 New Super")
    def test_patch_init_super(self):
        class Person(object):
            def __init__(self):
                self.base_prop = 'yo'

        class Artist(Person):
            def __init__(self):
                super().__init__()
                self.prop = 'old'

        patchy.patch(Artist.__init__, """\
            @@ -1,3 +1,3 @@
             def __init__(self):
                 super().__init__()
            -    self.prop = 'old'
            +    self.prop = 'new'""")

        a = Artist()
        assert a.base_prop == 'yo'
        assert a.prop == 'new'

    def test_patch_freevars(self):
        def free_func(v):
            return v + ' on toast'

        def sample():
            filling = 'Chalk'
            return free_func(filling)

        patchy.patch(sample, """\
            @@ -1,2 +1,2 @@
             def method():
            -    filling = 'Chalk'
            +    filling = 'Cheese'
                 return free_func(filling)
            """)

        assert sample() == "Cheese on toast"

    def test_patch_freevars_order(self):
        def tastes_good(v):
            return v + ' tastes good'

        def tastes_bad(v):
            return v + ' tastes bad'

        def sample():
            return ', '.join([
                tastes_good('Cheese'),
                tastes_bad('Chalk'),
            ])

        patchy.patch(sample, """\
            @@ -1,4 +1,4 @@
             def sample():
                 return ', '.join([
            -        tastes_good('Cheese'),
            -        tastes_bad('Chalk'),
            +        tastes_bad('Chalk'),
            +        tastes_good('Cheese'),
                 )]
            """)

        assert sample() == 'Chalk tastes bad, Cheese tastes good'

    def test_patch_freevars_remove(self):
        def tastes_good(v):
            return v + ' tastes good'

        def tastes_bad(v):
            return v + ' tastes bad'

        def sample():
            return ', '.join([
                tastes_bad('Chalk'),
                tastes_good('Cheese'),
            ])

        patchy.patch(sample, """\
            @@ -1,5 +1,4 @@
             def sample():
                 return ', '.join([
            -        tastes_bad('Chalk'),
                     tastes_good('Cheese'),
                 ])
            """)

        assert sample() == 'Cheese tastes good'

    def test_patch_freevars_nested(self):
        def free_func(v):
            return v + ' on toast'

        def sample():
            filling = 'Chalk'

            def _inner_func():
                return free_func(filling)

            return _inner_func

        patchy.patch(sample, """\
            @@ -1,2 +1,2 @@
             def sample():
            -    filling = 'Chalk'
            +    filling = 'Cheese'

                 def _inner_func():
            """)

        assert sample()() == "Cheese on toast"

    @pytest.mark.xfail(raises=NameError)
    def test_patch_freevars_re_close(self):
        def nasty_filling(v):
            return 'Chalk'

        def nice_filling(v):
            return 'Cheese'

        def sample():
            filling = nasty_filling()
            return filling + ' on toast'

        patchy.patch(sample, """\
            @@ -1,2 +1,2 @@
             def sample():
            -    filling = nasty_filling()
            +    filling = nice_filling()
                 return filling + ' on toast'
            """)

        assert sample() == "Cheese on toast"

    def test_patch_instancemethod_twice(self):
        class Artist(object):
            def method(self):
                return 'Chalk'

        patchy.patch(Artist.method, """\
            @@ -1,2 +1,2 @@
             def method(self):
            -    return 'Chalk'
            +    return 'Cheese'""")

        patchy.patch(Artist.method, """\
            @@ -1,2 +1,2 @@
             def method(self):
            -    return 'Cheese'
            +    return 'Crackers'""")

        assert Artist().method() == "Crackers"

    def test_patch_instancemethod_mangled(self):
        class Artist(object):
            def __mangled_name(self, v):
                return v + ' on toast'

            def method(self):
                filling = 'Chalk'
                return self.__mangled_name(filling)

        patchy.patch(Artist.method, """\
            @@ -1,2 +1,2 @@
             def method(self):
            -    filling = 'Chalk'
            +    filling = 'Cheese'
                 return self.__mangled_name(filling)
            """)

        assert Artist().method() == "Cheese on toast"

    def test_patch_old_class_instancemethod_mangled(self):
        class Artist:
            def __mangled_name(self, v):
                return v + ' on toast'

            def method(self):
                filling = 'Chalk'
                return self.__mangled_name(filling)

        patchy.patch(Artist.method, """\
            @@ -1,2 +1,2 @@
             def method(self):
            -    filling = 'Chalk'
            +    filling = 'Cheese'
                 return self.__mangled_name(filling)
            """)

        assert Artist().method() == "Cheese on toast"

    def test_patch_instancemethod_mangled_freevars(self):
        def _Artist__mangled_name(v):
            return v + ' on '

        def plain_name(v):
            return v + 'toast'

        class Artist:
            def method(self):
                filling = 'Chalk'
                return plain_name(__mangled_name(filling))  # noqa: F821

        patchy.patch(Artist.method, """\
            @@ -1,2 +1,2 @@
             def method(self):
            -    filling = 'Chalk'
            +    filling = 'Cheese'
                 return plain_name(__mangled_name(filling))  # noqa: F821
            """)

        assert Artist().method() == "Cheese on toast"

    def test_patch_instancemethod_mangled_tabs(self, tmpdir):
        tmpdir.join('tabs_mangled.py').write(dedent("""\
            class Artist:
            \tdef __mangled_name(self, v):
            \t\treturn v + ' on toast'

            \tdef method(self):
            \t\tfilling = 'Chalk'
            \t\treturn self.__mangled_name(filling)
        """))
        sys.path.insert(0, six.text_type(tmpdir))

        try:
            from tabs_mangled import Artist
        finally:
            sys.path.pop()

        patchy.patch(Artist.method, """\
            @@ -1,2 +1,2 @@
             def method(self):
            -\tfilling = 'Chalk'
            +\tfilling = 'Cheese'
            \treturn __mangled_name(filling)
            """)

        assert Artist().method() == "Cheese on toast"

    def test_patch_init(self):
        class Artist(object):
            def __init__(self):
                self.prop = 'old'

        patchy.patch(Artist.__init__, """\
            @@ -1,2 +1,2 @@
             def __init__(self):
            -    self.prop = 'old'
            +    self.prop = 'new'""")

        a = Artist()
        assert a.prop == 'new'

    def test_patch_init_change_arg(self):
        class Artist(object):
            def __init__(self):
                self.prop = 'old'

        patchy.patch(Artist.__init__, """\
            @@ -1,2 +1,2 @@
            -def __init__(self):
            -    self.prop = 'old'
            +def __init__(self, arg):
            +    self.prop = arg""")

        a = Artist('new')
        assert a.prop == 'new'

    def test_patch_classmethod(self):
        class Emotion(object):
            def __init__(self, name):
                self.name = name

            @classmethod
            def create(cls, name):
                return cls(name)

        patchy.patch(Emotion.create, """\
            @@ -1,2 +1,3 @@
             @classmethod
             def create(cls, name):
            +    name = name.title()
                 return cls(name)""")

        assert Emotion.create("Happy").name == "Happy"
        assert Emotion.create("happy").name == "Happy"

    def test_patch_classmethod_twice(self):
        class Emotion(object):
            def __init__(self, name):
                self.name = name

            @classmethod
            def create(cls, name):
                return cls(name)

        patchy.patch(Emotion.create, """\
            @@ -1,2 +1,3 @@
             @classmethod
             def create(cls, name):
            +    name = name.title()
                 return cls(name)""")

        patchy.patch(Emotion.create, """\
            @@ -1,3 +1,3 @@
             @classmethod
             def create(cls, name):
            -    name = name.title()
            +    name = name.lower()
                 return cls(name)""")

        assert Emotion.create("happy").name == "happy"
        assert Emotion.create("Happy").name == "happy"
        assert Emotion.create("HAPPY").name == "happy"

    def test_patch_staticmethod(self):
        class Doge(object):
            @staticmethod
            def bark():
                return "Woof"

        patchy.patch(Doge.bark, """\
            @@ -1,3 +1,3 @@
             @staticmethod
             def bark():
            -    return "Woof"
            +    return "Wow\"""")

        assert Doge.bark() == "Wow"

    def test_patch_staticmethod_twice(self):
        class Doge(object):
            @staticmethod
            def bark():
                return "Woof"

        patchy.patch(Doge.bark, """\
            @@ -1,3 +1,3 @@
             @staticmethod
             def bark():
            -    return "Woof"
            +    return "Wow\"""")

        patchy.patch(Doge.bark, """\
            @@ -1,3 +1,3 @@
             @staticmethod
             def bark():
            -    return "Wow"
            +    return "Wowowow\"""")

        assert Doge.bark() == "Wowowow"

    @unittest.skipUnless(six.PY2, "Python 2")
    def test_patch_future(self):
        from .python2_future import sample

        assert sample() is six.text_type

        patchy.patch(sample, """\
            @@ -1,2 +1,3 @@
             def sample():
            +    pass
                 return type('example string')
            """)

        assert sample() is six.text_type

    @unittest.skipUnless(six.PY2, "Python 2")
    def test_patch_future_twice(self):
        from .python2_future import sample2

        assert sample2() is six.text_type

        patchy.patch(sample2, """\
            @@ -1,2 +1,3 @@
             def sample2():
            +    pass
                 return type('example string 2')
            """)

        assert sample2() is six.text_type

        patchy.patch(sample2, """\
            @@ -1,3 +1,4 @@
             def sample2():
                 pass
            +    pass
                 return type('example string 2')
            """)

        assert sample2() is six.text_type

    @unittest.skipUnless(six.PY2, "Python 2")
    def test_patch_future_doesnt_inherit(self):
        # This test module has 'division' imported, but python2_future doesn't
        assert division
        from .python2_future import sample3

        assert sample3() == 0

        patchy.patch(sample3, """\
            @@ -1,2 +1,3 @@
             def sample3():
            +    pass
                 return 1 / 2
            """)

        assert sample3() == 0

    @unittest.skipUnless(six.PY2, "Python 2")
    def test_patch_future_instancemethod(self):
        from .python2_future import Sample

        assert Sample().meth() is six.text_type

        patchy.patch(Sample.meth, """\
            @@ -1,2 +1,3 @@
             def meth(self):
            +    pass
                 return type('example string')
            """)

        assert Sample().meth() is six.text_type

    @pytest.mark.skipif(not six.PY3, reason="Python 3 only")
    def test_patch_nonlocal_fails(self, tmpdir):
        # Put in separate file since it would SyntaxError on Python 2
        tmpdir.join('py3_nonlocal.py').write(dedent("""\
            variab = 20


            def get_function():
                variab = 15

                def sample():
                    nonlocal variab
                    multiple = 3
                    return variab * multiple

                return sample

            sample = get_function()
        """))
        sys.path.insert(0, six.text_type(tmpdir))
        try:
            from py3_nonlocal import sample
        finally:
            sys.path.pop()

        assert sample() == 15 * 3

        patchy.patch(sample, """\
            @@ -2,3 +2,3 @@
                 nonlocal variab
            -    multiple = 3
            +    multiple = 4
            """)

        assert sample() == 15 * 4


class UnpatchTests(PatchyTestCase):

    def test_unpatch(self):
        def sample():
            return 9001

        patchy.unpatch(sample, """\
            @@ -1,2 +1,2 @@
             def sample():
            -    return 1
            +    return 9001
            """)
        assert sample() == 1

    def test_unpatch_invalid_unreversed(self):
        """
        We need to balk on patches that fail on application
        """
        def sample():
            return 1

        # This patch would make sense forwards but doesn't backwards
        bad_patch = """\
            @@ -1,2 +1,2 @@
             def sample():
            -    return 1
            +    return 2"""
        with pytest.raises(ValueError) as excinfo:
            patchy.unpatch(sample, bad_patch)

        assert "Unreversed patch detected!" in str(excinfo.value)
        assert sample() == 1

    def test_unpatch_invalid_hunk(self):
        """
        We need to balk on patches that fail on application
        """
        def sample():
            return 1

        # This patch would make sense forwards but doesn't backwards
        bad_patch = """\
            @@ -1,2 +1,2 @@
             def sample():
            -    return 3
            +    return 2"""
        with pytest.raises(ValueError) as excinfo:
            patchy.unpatch(sample, bad_patch)

        assert "Hunk #1 FAILED" in str(excinfo.value)
        assert sample() == 1


class BothTests(PatchyTestCase):

    def test_patch_unpatch(self):
        def sample():
            return 1

        patch_text = """\
            @@ -1,2 +1,2 @@
             def sample():
            -    return 1
            +    return 9001
            """

        patchy.patch(sample, patch_text)
        assert sample() == 9001

        # Check that we use the cache
        orig_mkdtemp = patchy.api.mkdtemp

        def mkdtemp(*args, **kwargs):
            raise AssertionError(
                "mkdtemp should not be called, the unpatch should be cached."
            )

        try:
            patchy.api.mkdtemp = mkdtemp
            patchy.unpatch(sample, patch_text)
        finally:
            patchy.api.mkdtemp = orig_mkdtemp
        assert sample() == 1

        # Check that we use the cache going forwards again
        try:
            patchy.api.mkdtemp = mkdtemp
            patchy.patch(sample, patch_text)
        finally:
            patchy.api.mkdtemp = orig_mkdtemp
        assert sample() == 9001


class TempPatchTests(PatchyTestCase):

    def test_context_manager(self):
        def sample():
            return 1234

        patch_text = """\
            @@ -1,2 +1,2 @@
             def sample():
            -    return 1234
            +    return 5678
            """

        assert sample() == 1234
        with patchy.temp_patch(sample, patch_text):
            assert sample() == 5678
        assert sample() == 1234

    def test_decorator(self):
        def sample():
            return 3456

        patch_text = """\
            @@ -1,2 +1,2 @@
             def sample():
            -    return 3456
            +    return 7890
            """

        @patchy.temp_patch(sample, patch_text)
        def decorated():
            assert sample() == 7890

        assert sample() == 3456
        decorated()
        assert sample() == 3456
