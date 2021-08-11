import random
from typing import Dict, Tuple


class PatchingCache:
    def __init__(self, maxsize: int) -> None:
        self.maxsize = maxsize
        self._cache: Dict[Tuple[str, str, bool], str] = {}

    def clear(self) -> None:
        self._cache = {}

    def retrieve(self, source: str, patch_text: str, forwards: bool) -> str:
        return self._cache[(source, patch_text, forwards)]

    def store(
        self, source: str, patch_text: str, forwards: bool, new_source: str
    ) -> None:
        if len(self._cache) + 2 > self.maxsize:
            # Delete a random 25%, at least 2
            delete_count = max(2, len(self._cache) // 4)
            to_delete = random.sample(list(self._cache.keys()), delete_count)
            for key in to_delete:
                del self._cache[key]

        # Cache in both directions - makes reversal faster
        self._cache[(source, patch_text, forwards)] = new_source
        other_direction = not forwards
        self._cache[(new_source, patch_text, other_direction)] = source
