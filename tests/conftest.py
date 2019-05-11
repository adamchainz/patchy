import pytest

import patchy.api


@pytest.fixture(autouse=True)
def clear_cache():
    patchy.api._patching_cache.clear()
