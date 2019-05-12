import patchy
import patchy.api


def test_patch_unpatch():
    def sample():
        return 1

    patch_text = """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return 1
        +    return 9001
        """

    patchy.patch(sample, patch_text)
    assert sample() == 9001

    # Check that we use the cache
    orig_mkdtemp = patchy.api.mkdtemp

    def mkdtemp(*args, **kwargs):
        raise AssertionError(
            "mkdtemp should not be called, the unpatch should be cached."
        )

    try:
        patchy.api.mkdtemp = mkdtemp
        patchy.unpatch(sample, patch_text)
    finally:
        patchy.api.mkdtemp = orig_mkdtemp
    assert sample() == 1

    # Check that we use the cache going forwards again
    try:
        patchy.api.mkdtemp = mkdtemp
        patchy.patch(sample, patch_text)
    finally:
        patchy.api.mkdtemp = orig_mkdtemp
    assert sample() == 9001
