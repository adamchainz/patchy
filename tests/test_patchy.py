#!/usr/bin/env python
# -*- coding: utf-8 -*-
import six
import unittest
from textwrap import dedent

import patchy


class TestPatchy(unittest.TestCase):

    def test_replace(self):
        def sample():
            return 1

        self.assertEqual(sample(), 1)
        patchy.replace(sample, find='1', replace='2')
        self.assertEqual(sample(), 2)

    def test_replace_multiline(self):
        def sample(arg1):
            output = arg1 * 5
            return output

        self.assertEqual(sample('Snoo'), 'SnooSnooSnooSnooSnoo')
        patchy.replace(sample, find='* 5', replace='* 2')
        self.assertEqual(sample('Snoo'), 'SnooSnoo')

    def test_replace_class(self):
        class Artist(object):
            def method(self):
                return 'Chalk'

        patchy.replace(Artist.method, 'Chalk', 'Watercolour')
        self.assertEqual(Artist().method(), 'Watercolour')

    def test_replace_invalid(self):
        def sample():
            return "A"

        with self.assertRaises(ValueError):
            patchy.replace(sample, find='B', replace='C')

    def test_replace_count(self):
        def sample():
            return 2 * 2

        patchy.replace(sample, '2', '4', count=2)
        self.assertEqual(sample(), 16)

    def test_replace_count_bad(self):
        def sample():
            return 2 * 1

        with self.assertRaises(ValueError):
            patchy.replace(sample, '2', '4', count=2)

    def test_replace_twice(self):
        def sample():
            return 1

        patchy.replace(sample, '1', '2')
        patchy.replace(sample, '2', '3')
        self.assertEqual(sample(), 3)

    def test_patch(self):
        def sample():
            return 1

        patchy.patch(
            sample,
            """\
@@ -1,2 +1,2 @@
 def sample():
-    return 1
+    return 2"""
        )
        self.assertEqual(sample(), 2)

    def test_patch_simple(self):
        def sample():
            return 1

        patchy.patch(
            sample,
            """\
@@ -2,2 +2,2 @@
-    return 1
+    return 2
"""
        )
        self.assertEqual(sample(), 2)

    def test_patch_simple_no_newline(self):
        def sample():
            return 1

        patchy.patch(
            sample,
            """\
@@ -2,2 +2,2 @@
-    return 1
+    return 2"""
        )
        self.assertEqual(sample(), 2)

    def test_patch_invalid(self):
        """
        We need to balk on empty patches
        """
        def sample():
            return 1

        bad_patch = """
            """
        with self.assertRaises(ValueError) as cm:
            patchy.patch(sample, bad_patch)

        msg = str(cm.exception)
        self.assertEqual(msg, "Invalid patch.", )
        self.assertEqual(sample(), 1)

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
        with self.assertRaises(ValueError) as cm:
            patchy.patch(sample, bad_patch)

        msg = str(cm.exception)
        self.assertIn("Hunk #1 FAILED", msg)
        self.assertEqual(sample(), 1)

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
+    return 3""")

        self.assertEqual(sample(), 3)

    def test_patch_instancemethod(self):
        class Artist(object):
            def method(self):
                return 'Chalk'

        patchy.patch(Artist.method, """\
@@ -1,2 +1,2 @@
 def method(self):
-    return 'Chalk'
+    return 'Cheese'""")

        self.assertEqual(Artist().method(), "Cheese")

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

        self.assertEqual(Artist().method(), "Crackers")

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

        self.assertEqual(Emotion.create("Happy").name, "Happy")
        self.assertEqual(Emotion.create("happy").name, "Happy")

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

        self.assertEqual(Emotion.create("happy").name, "happy")
        self.assertEqual(Emotion.create("Happy").name, "happy")
        self.assertEqual(Emotion.create("HAPPY").name, "happy")

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

        self.assertEqual(Doge.bark(), "Wow")

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

        self.assertEqual(Doge.bark(), "Wowowow")

    @unittest.skipUnless(six.PY3, "Python 3")
    @unittest.expectedFailure
    def test_replace_nonlocal(self):
        unittest = 5  # shadow a global name

        # Using exec because 'nonlocal' would SyntaxError when testing on 2.7
        sample = six.exec_(dedent("""\
            def sample():
                nonlocal unittest
                multiple = 3
                return multiple * unittest"""), globals(), locals())['sample']

        patchy.replace(sample, find='multiple = 3', replace='multiple = 4')
        self.assertEqual(sample(), 20)

if __name__ == '__main__':
    unittest.main()
