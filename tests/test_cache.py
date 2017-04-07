# -*- encoding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals


import pytest

from patchy.cache import PatchingCache
from .base import PatchyTestCase


class TestPatchingCache(PatchyTestCase):
    def test_store_retrieve(self):
        cache = PatchingCache(maxsize=100)
        cache.store("a", "b", True, "c")
        assert cache.retrieve("a", "b", True) == "c"
        assert cache.retrieve("c", "b", False) == "a"

    def test_missing_key_error(self):
        cache = PatchingCache(maxsize=100)
        with pytest.raises(KeyError):
            cache.retrieve("a", "b", True)

    def test_clear(self):
        cache = PatchingCache(maxsize=100)
        cache.store("a", "b", True, "c")
        cache.clear()
        with pytest.raises(KeyError):
            cache.retrieve("a", "b", True)

    def test_culling(self):
        cache = PatchingCache(maxsize=4)
        cache.store("a", "b", True, "c")
        assert len(cache._cache) == 2
        cache.store("a", "d", True, "e")
        assert len(cache._cache) == 4
        cache.store("a", "f", True, "g")
        assert len(cache._cache) <= 4
