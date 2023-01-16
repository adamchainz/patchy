from __future__ import annotations

import pytest

import patchy.api


def test_unpatch():
    def sample() -> int:
        return 9001

    sample()

    patchy.unpatch(
        sample,
        """\
        @@ -1,2 +1,2 @@
         def sample() -> int:
        -    return 1
        +    return 9001
        """,
    )
    assert sample() == 1


def test_unpatch_invalid_unreversed():
    """
    We need to balk on patches that fail on application
    """

    def sample() -> int:
        return 1

    # This patch would make sense forwards but doesn't backwards
    bad_patch = """\
        @@ -1,2 +1,2 @@
         def sample() -> int:
        -    return 1
        +    return 2"""
    with pytest.raises(ValueError) as excinfo:
        patchy.unpatch(sample, bad_patch)

    msg = str(excinfo.value)
    assert (
        # GNU patch
        "Unreversed patch detected!" in msg
        # BSD patch
        or msg.startswith("Could not unapply the patch")
    )
    assert sample() == 1


def test_unpatch_invalid_hunk():
    """
    We need to balk on patches that fail on application
    """

    def sample() -> int:
        return 1

    bad_patch = """\
        @@ -1,2 +1,2 @@
         def sample() -> int:
        -    return 3
        +    return 2"""
    with pytest.raises(ValueError) as excinfo:
        patchy.unpatch(sample, bad_patch)

    msg = str(excinfo.value)
    assert (
        # GNU patch
        "Hunk #1 FAILED" in msg
        # BSD patch
        or "1 out of 1 hunks failed" in msg
    )
    assert sample() == 1
