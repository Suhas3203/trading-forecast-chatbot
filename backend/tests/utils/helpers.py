"""Common test helpers — retries, soft assertions, and data utilities.
Sourced from Testing COE greenfield_framework/pytest/utils/helpers.py
"""

import time
from typing import Callable, Any


def retry(fn: Callable, retries: int = 3, delay: float = 1.0, exceptions=(Exception,)) -> Any:
    """Retry a callable up to `retries` times on specified exceptions."""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except exceptions as e:
            last_exc = e
            if attempt < retries:
                time.sleep(delay)
    raise last_exc


class SoftAssert:
    """Collect multiple assertion failures and report them all at the end."""

    def __init__(self):
        self._failures: list[str] = []

    def check(self, condition: bool, message: str):
        if not condition:
            self._failures.append(message)

    def assert_all(self):
        if self._failures:
            summary = "\n".join(f"  - {f}" for f in self._failures)
            raise AssertionError(f"{len(self._failures)} assertion(s) failed:\n{summary}")
