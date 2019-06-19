import pytest

import patchy
import patchy.api


def test_unpatch():
    def sample():
        return 9001

    patchy.unpatch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return 1
        +    return 9001
        """,
    )
    assert sample() == 1


def test_unpatch_invalid_unreversed():
    """
    We need to balk on patches that fail on application
    """

    def sample():
        return 1

    # This patch would make sense forwards but doesn't backwards
    bad_patch = """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return 1
        +    return 2"""
    with pytest.raises(ValueError) as excinfo:
        patchy.unpatch(sample, bad_patch)

    assert "Unreversed patch detected!" in str(excinfo.value)
    assert sample() == 1


def test_unpatch_invalid_hunk():
    """
    We need to balk on patches that fail on application
    """

    def sample():
        return 1

    # This patch would make sense forwards but doesn't backwards
    bad_patch = """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return 3
        +    return 2"""
    with pytest.raises(ValueError) as excinfo:
        patchy.unpatch(sample, bad_patch)

    assert "Hunk #1 FAILED" in str(excinfo.value)
    assert sample() == 1
