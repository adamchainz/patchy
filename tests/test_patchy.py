# -*- coding: utf-8 -*-
from __future__ import division, print_function

import unittest

import pytest
import six

import patchy
import patchy.api

from .base import PatchyTestCase

if six.PY3:
    # For linting purposes only
    unicode = None


class PatchTests(PatchyTestCase):

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

        print(excinfo.value)
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

    @unittest.skipUnless(six.PY3, "Python 3")
    def test_patch_nonlocal_fails(self):
        # Kept in separate file since it would SyntaxError on Python 2
        from .py3_nonlocal import sample

        with pytest.raises(SyntaxError) as excinfo:
            patchy.patch(sample, """\
                @@ -2,3 +2,3 @@
                     nonlocal variab
                -    multiple = 3
                +    multiple = 4
                """)
        assert "no binding for nonlocal 'variab' found" in str(excinfo.value)

    @unittest.skipUnless(six.PY2, "Python 2")
    def test_patch_future(self):
        from .python2_future import sample

        assert sample() is unicode

        patchy.patch(sample, """\
            @@ -1,2 +1,3 @@
             def sample():
            +    pass
                 return type('example string')
            """)

        assert sample() is unicode

    @unittest.skipUnless(six.PY2, "Python 2")
    def test_patch_future_twice(self):
        from .python2_future import sample2

        assert sample2() is unicode

        patchy.patch(sample2, """\
            @@ -1,2 +1,3 @@
             def sample2():
            +    pass
                 return type('example string 2')
            """)

        assert sample2() is unicode

        patchy.patch(sample2, """\
            @@ -1,3 +1,4 @@
             def sample2():
                 pass
            +    pass
                 return type('example string 2')
            """)

        assert sample2() is unicode

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

        assert Sample().meth() is unicode

        patchy.patch(Sample.meth, """\
            @@ -1,2 +1,3 @@
             def meth(self):
            +    pass
                 return type('example string')
            """)

        assert Sample().meth() is unicode


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
