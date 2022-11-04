from __future__ import annotations

import pytest

import patchy.api


def test_replace():
    def sample() -> int:
        return 1

    assert sample() == 1

    patchy.replace(
        sample,
        """\
        def sample() -> int:
            return 1
        """,
        """\
        def sample() -> int:
            return 42
        """,
    )

    assert sample() == 42


def test_replace_only_cares_about_ast():
    def sample() -> int:
        return 1

    assert sample() == 1

    patchy.replace(
        sample, "def sample() -> int: return 1", "def sample() -> int: return 42"
    )

    assert sample() == 42


def test_replace_twice():
    def sample() -> int:
        return 1

    assert sample() == 1

    patchy.replace(
        sample, "def sample() -> int: return 1", "def sample() -> int: return 2"
    )
    patchy.replace(
        sample, "def sample() -> int: return 2", "def sample() -> int: return 3"
    )

    assert sample() == 3


def test_replace_mutable_default_arg():
    def foo(append: str | None = None, mutable: list[str] = []) -> int:  # noqa: B006
        if append is not None:
            mutable.append(append)
        return len(mutable)

    assert foo() == 0
    assert foo("v1") == 1
    assert foo("v2") == 2
    assert foo(mutable=[]) == 0

    patchy.replace(
        foo,
        """\
        def foo(append: str | None = None, mutable: list[str] = []) -> int:
            if append is not None:
                mutable.append(append)
            return len(mutable)
        """,
        """\
        def foo(append: str | None = None, mutable: list[str] = []) -> int:
            len(mutable)
            if append is not None:
                mutable.append(append)
            return len(mutable)
        """,
    )

    assert foo() == 2
    assert foo("v3") == 3
    assert foo(mutable=[]) == 0


def test_replace_instancemethod():
    class Artist:
        def method(self) -> str:
            return "Chalk"

    assert Artist().method() == "Chalk"

    patchy.replace(
        Artist.method,
        """\
        def method(self) -> str:
            return 'Chalk'
        """,
        """\
        def method(self) -> str:
            return 'Cheese'
        """,
    )

    assert Artist().method() == "Cheese"


def test_replace_unexpected_source():
    def sample() -> int:
        return 2

    assert sample() == 2

    with pytest.raises(ValueError) as excinfo:
        patchy.replace(
            sample,
            """\
            def sample() -> int:
                return 1
            """,
            """\
            def sample() -> int:
                return 42
            """,
        )

    msg = str(excinfo.value)
    assert "The code of 'sample' has changed from expected" in msg
    assert "return 2" in msg
    assert "return 1" in msg


def test_replace_no_expected_source():
    def sample() -> int:
        return 2

    assert sample() == 2

    patchy.replace(
        sample,
        None,
        """\
        def sample() -> int:
            return 42
        """,
    )

    assert sample() == 42
