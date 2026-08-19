from __future__ import annotations

from typing import Any

import patchy.api


def test_patch_unpatch():
    def sample() -> int:
        return 1

    assert sample() == 1

    patch_text = """\
        @@ -1,2 +1,2 @@
         def sample() -> int:
        -    return 1
        +    return 9001
        """

    patchy.patch(sample, patch_text)
    assert sample() == 9001

    # Check that we use the cache
    orig_apply_patch = patchy.api.apply_patch  # type: ignore [attr-defined]

    def apply_patch(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
        raise AssertionError(
            "apply_patch should not be called, the unpatch should be cached."
        )

    try:
        patchy.api.apply_patch = apply_patch  # type: ignore [attr-defined,assignment]
        patchy.unpatch(sample, patch_text)
    finally:
        patchy.api.apply_patch = orig_apply_patch  # type: ignore [attr-defined]
    assert sample() == 1

    # Check that we use the cache going forwards again
    try:
        patchy.api.apply_patch = apply_patch  # type: ignore [attr-defined,assignment]
        patchy.patch(sample, patch_text)
    finally:
        patchy.api.apply_patch = orig_apply_patch  # type: ignore [attr-defined]
    assert sample() == 9001
