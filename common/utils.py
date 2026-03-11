"""Shared utility functions."""

from __future__ import annotations
import time
import asyncio
from typing import Any, Callable, TypeVar
from functools import wraps

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

T = TypeVar("T")


def retry_async(max_attempts: int = 3, min_wait: float = 1.0, max_wait: float = 10.0):
    """Decorator for async functions with exponential backoff retry."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )


def truncate(text: str, max_length: int = 500) -> str:
    """Truncate text to max_length characters."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def safe_get(d: dict, *keys: str, default: Any = None) -> Any:
    """Safely navigate nested dict keys."""
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key, default)
    return d


async def measure_ms(coro) -> tuple[Any, float]:
    """Measure async coroutine execution time in milliseconds."""
    start = time.perf_counter()
    result = await coro
    elapsed = (time.perf_counter() - start) * 1000
    return result, elapsed


def build_error_response(code: str, message: str, status_code: int = 500) -> dict:
    return {"error": {"code": code, "message": message}, "status_code": status_code}
