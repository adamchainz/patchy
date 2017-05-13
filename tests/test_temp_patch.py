# -*- encoding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import patchy
import patchy.api


def test_context_manager():
    def sample():
        return 1234

    patch_text = """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return 1234
        +    return 5678
        """

    assert sample() == 1234
    with patchy.temp_patch(sample, patch_text):
        assert sample() == 5678
    assert sample() == 1234


def test_decorator():
    def sample():
        return 3456

    patch_text = """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return 3456
        +    return 7890
        """

    @patchy.temp_patch(sample, patch_text)
    def decorated():
        assert sample() == 7890

    assert sample() == 3456
    decorated()
    assert sample() == 3456
