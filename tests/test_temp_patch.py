import sys
from textwrap import dedent

import patchy
import patchy.api


def test_context_manager():
    """
    Returns the test context manager.

    Args:
    """
    def sample():
        """
        Return a sample of the current sample.

        Args:
        """
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
    """
    Decorator for test test test.

    Args:
    """
    def sample():
        """
        Sample a new sample

        Args:
        """
        return 3456

    patch_text = """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return 3456
        +    return 7890
        """

    @patchy.temp_patch(sample, patch_text)
    def decorated():
        """
        Decorator to ensure the given the input.

        Args:
        """
        assert sample() == 7890

    assert sample() == 3456
    decorated()
    assert sample() == 3456


def test_patch_by_path(tmpdir):
    """
    Patch a testdir exists.

    Args:
        tmpdir: (str): write your description
    """
    package = tmpdir.mkdir("tmp_by_path_pkg")
    package.join("__init__.py").ensure(file=True)
    package.join("mod.py").write(
        dedent(
            """\
        class Foo(object):
            def sample(self):
                return 1
        """
        )
    )
    sys.path.insert(0, str(tmpdir))
    patch_text = """\
        @@ -2,2 +2,2 @@
        -    return 1
        +    return 2
        """

    try:
        with patchy.temp_patch("tmp_by_path_pkg.mod.Foo.sample", patch_text):
            from tmp_by_path_pkg.mod import Foo

            assert Foo().sample() == 2
    finally:
        sys.path.pop(0)

    assert Foo().sample() == 1
