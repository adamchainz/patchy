# -*- encoding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest
import six

import patchy.api


@pytest.fixture(autouse=True)
def clear_cache():
    patchy.api._patching_cache.clear()


skip_unless_python_2 = pytest.mark.skipif(not six.PY2, reason="Python 2 only")
skip_unless_python_3 = pytest.mark.skipif(not six.PY3, reason="Python 3 only")
