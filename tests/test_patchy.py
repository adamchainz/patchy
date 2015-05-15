#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

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
            """
            @@ -1,2 +1,2 @@
             def sample():
            -    return 1
            +    return 2
            """
        )
        self.assertEqual(sample(), 2)

    def test_patch_simple(self):
        def sample():
            return 1

        patchy.patch(
            sample,
            """
            @@ -2,2 +2,2 @@
            -    return 1
            +    return 2
            """
        )
        self.assertEqual(sample(), 2)

    def test_patch_invalid(self):
        """
        We need to balk on patches that are not applicable
        """
        def sample():
            return 1

        with self.assertRaises(ValueError):
            patchy.patch(
                sample,
                """
                @@ -1,2 +1,2 @@
                 def sample():
                -    return 2
                +    return 23
                """
            )

        self.assertEqual(sample(), 1)


if __name__ == '__main__':
    unittest.main()
