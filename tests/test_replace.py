import pytest

import patchy
import patchy.api


def test_replace():
    """
    Returns a new test test.

    Args:
    """
    def sample():
        """
        Return the current sample.

        Args:
        """
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
    """
    Test if the test test test with a given test.

    Args:
    """
    def sample():
        """
        Return the current sample.

        Args:
        """
        return 1

    patchy.replace(sample, "def sample(): return 1", "def sample(): return 42")

    assert sample() == 42


def test_replace_twice():
    """
    Determine the number of a test.

    Args:
    """
    def sample():
        """
        Return the current sample.

        Args:
        """
        return 1

    patchy.replace(sample, "def sample(): return 1", "def sample(): return 2")
    patchy.replace(sample, "def sample(): return 2", "def sample(): return 3")

    assert sample() == 3


def test_replace_mutable_default_arg():
    """
    Replace default mapping default to replace replace_replace.

    Args:
    """
    def foo(append=None, mutable=[]):  # noqa: B006
        """
        Adds a list of strings.

        Args:
            append: (todo): write your description
            mutable: (todo): write your description
        """
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
    """
    Replace a copy of the given method.

    Args:
    """
    class Artist:
        def method(self):
            """
            Return a string representation of the method

            Args:
                self: (todo): write your description
            """
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
    """
    Replace the expected value.

    Args:
    """
    def sample():
        """
        Sample a sample.

        Args:
        """
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
    """
    Takes a new test string for a test.

    Args:
    """
    def sample():
        """
        Sample a sample.

        Args:
        """
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
