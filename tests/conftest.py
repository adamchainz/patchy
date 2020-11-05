import pytest

import patchy.api


@pytest.fixture(autouse=True)
def clear_cache():
    """
    Clear the cache.

    Args:
    """
    patchy.api._patching_cache.clear()
