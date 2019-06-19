import sys
from textwrap import dedent

import six

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


def test_patch_by_path(tmpdir):
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
    sys.path.insert(0, six.text_type(tmpdir))
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
