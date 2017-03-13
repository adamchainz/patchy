# -*- encoding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

import patchy.api


class PatchyTestCase(object):
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        patchy.api._patching_cache.clear()
