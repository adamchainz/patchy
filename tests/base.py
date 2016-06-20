# -*- encoding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

import patchy.api


class PatchyTestCase(unittest.TestCase):
    def setUp(self):
        patchy.api._patching_cache.clear()
