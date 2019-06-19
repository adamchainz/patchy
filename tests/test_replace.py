import pytest

import patchy
import patchy.api


def test_replace():
    def sample():
        return 1

    patchy.replace(
        sample,
        """\
        def sample():
            return 1
        """,
        """\
        def sample():
            return 42
        """,
    )

    assert sample() == 42


def test_replace_only_cares_about_ast():
    def sample():
        return 1

    patchy.replace(sample, "def sample(): return 1", "def sample(): return 42")

    assert sample() == 42


def test_replace_twice():
    def sample():
        return 1

    patchy.replace(sample, "def sample(): return 1", "def sample(): return 2")
    patchy.replace(sample, "def sample(): return 2", "def sample(): return 3")

    assert sample() == 3


def test_replace_mutable_default_arg():
    def foo(append=None, mutable=[]):  # noqa: B006
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
        def foo(append=None, mutable=[]):
            if append is not None:
                mutable.append(append)
            return len(mutable)
        """,
        """\
        def foo(append=None, mutable=[]):
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
    class Artist(object):
        def method(self):
            return "Chalk"

    patchy.replace(
        Artist.method,
        """\
        def method(self):
            return 'Chalk'
        """,
        """\
        def method(self):
            return 'Cheese'
        """,
    )

    assert Artist().method() == "Cheese"


def test_replace_unexpected_source():
    def sample():
        return 2

    with pytest.raises(ValueError) as excinfo:
        patchy.replace(
            sample,
            """\
            def sample():
                return 1
            """,
            """\
            def sample():
                return 42
            """,
        )

    msg = str(excinfo.value)
    assert "The code of 'sample' has changed from expected" in msg
    assert "return 2" in msg
    assert "return 1" in msg


def test_replace_no_expected_source():
    def sample():
        return 2

    patchy.replace(
        sample,
        None,
        """\
        def sample():
            return 42
        """,
    )

    assert sample() == 42
