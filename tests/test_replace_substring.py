from __future__ import annotations

import pytest

import patchy.api


def test_replace_substring():
    def sample() -> int:
        return 1

    assert sample() == 1

    patchy.replace_substring(
        sample,
        """\
            return 1
        """,
        """\
            return 42
        """,
    )

    assert sample() == 42


def test_replace_substring_twice():
    def sample() -> int:
        return 1

    assert sample() == 1

    patchy.replace_substring(
        sample, "return 1", "return 2"
    )
    patchy.replace_substring(
        sample, "return 2", "return 3"
    )

    assert sample() == 3


def test_replace_substring_mutable_default_arg():
    def foo(append: str | None = None, mutable: list[str] = []) -> int:  # noqa: B006
        if append is not None:
            mutable.append(append)
        return len(mutable)

    assert foo() == 0
    assert foo("v1") == 1
    assert foo("v2") == 2
    assert foo(mutable=[]) == 0

    patchy.replace_substring(
        foo,
        """\
            if append is not None:
        """,
        """\
            len(mutable)
            if append is not None:
        """,
    )

    assert foo() == 2
    assert foo("v3") == 3
    assert foo(mutable=[]) == 0


def test_replace_substring_instancemethod():
    class Artist:
        def method(self) -> str:
            return "Chalk"

    assert Artist().method() == "Chalk"

    patchy.replace_substring(
        Artist.method,
        """\
            return 'Chalk'
        """,
        """\
            return 'Cheese'
        """,
    )

    assert Artist().method() == "Cheese"


def test_replace_substring_unexpected_source():
    def sample() -> int:
        return 2

    assert sample() == 2

    with pytest.raises(ValueError) as excinfo:
        patchy.replace_substring(
            sample,
            """\
                return 1
            """,
            """\
                return 42
            """,
        )

    msg = str(excinfo.value)
    assert "The code of 'sample' has changed from expected" in msg
    assert "return 2" in msg
    assert "return 1" in msg


def test_replace_substring_no_expected_source():
    def sample() -> int:
        return 2

    assert sample() == 2

    patchy.replace_substring(
        sample,
        None,
        """\
        def sample() -> int:
            return 42
        """,
    )

    assert sample() == 42
