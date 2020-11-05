import pytest

from patchy.cache import PatchingCache


def test_store_retrieve():
    """
    Retrieve the cache of - like object

    Args:
    """
    cache = PatchingCache(maxsize=100)
    cache.store("a", "b", True, "c")
    assert cache.retrieve("a", "b", True) == "c"
    assert cache.retrieve("c", "b", False) == "a"


def test_missing_key_error():
    """
    Retrieve the error for missing.

    Args:
    """
    cache = PatchingCache(maxsize=100)
    with pytest.raises(KeyError):
        cache.retrieve("a", "b", True)


def test_clear():
    """
    Clear the cache entries.

    Args:
    """
    cache = PatchingCache(maxsize=100)
    cache.store("a", "b", True, "c")
    cache.clear()
    with pytest.raises(KeyError):
        cache.retrieve("a", "b", True)


def test_culling():
    """
    Culling of the test.

    Args:
    """
    cache = PatchingCache(maxsize=4)
    cache.store("a", "b", True, "c")
    assert len(cache._cache) == 2
    cache.store("a", "d", True, "e")
    assert len(cache._cache) == 4
    cache.store("a", "f", True, "g")
    assert len(cache._cache) <= 4
