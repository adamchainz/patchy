import unittest

import patchy.api


class PatchyTestCase(unittest.TestCase):
    def setUp(self):
        patchy.api._patching_cache.clear()
