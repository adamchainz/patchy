from __future__ import annotations

import sys
from textwrap import dedent

import patchy.api


def test_context_manager():
    def sample() -> int:
        return 1234

    patch_text = """\
        @@ -1,2 +1,2 @@
         def sample() -> int:
        -    return 1234
        +    return 5678
        """

    assert sample() == 1234
    with patchy.temp_patch(sample, patch_text):
        assert sample() == 5678
    assert sample() == 1234


def test_decorator():
    def sample() -> int:
        return 3456

    patch_text = """\
        @@ -1,2 +1,2 @@
         def sample() -> int:
        -    return 3456
        +    return 7890
        """

    @patchy.temp_patch(sample, patch_text)
    def decorated() -> None:
        assert sample() == 7890

    assert sample() == 3456
    decorated()
    assert sample() == 3456


def test_patch_by_path(tmp_path):
    package = tmp_path / "tmp_by_path_pkg"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "mod.py").write_text(
        dedent(
            """\
        class Foo(object):
            def sample(self):
                return 1
        """
        )
    )
    patch_text = """\
        @@ -2,1 +2,1 @@
        -    return 1
        +    return 2
        """

    sys.path.insert(0, str(tmp_path))
    try:
        with patchy.temp_patch("tmp_by_path_pkg.mod.Foo.sample", patch_text):
            from tmp_by_path_pkg.mod import Foo

            assert Foo().sample() == 2
    finally:
        sys.path.pop(0)

    assert Foo().sample() == 1
