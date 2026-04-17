"""Retry logic and decorators using tenacity.

This module provides retry decorators configured for AAP API interactions,
with exponential backoff, jitter, and specific handling for different error types.
"""

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import httpx
from tenacity import (
    AsyncRetrying,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
)

from aap_migration.client.exceptions import NetworkError, RateLimitError, ServerError
from aap_migration.utils.logging import get_logger

logger = get_logger(__name__)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


def retry_on_network_error(
    max_attempts: int = 5, min_wait: int = 2, max_wait: int = 60
) -> Callable[[F], F]:
    """Retry decorator for network-related errors.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: F) -> F:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_random_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(
                (
                    httpx.NetworkError,
                    httpx.TimeoutException,
                    httpx.ConnectTimeout,
                    httpx.ReadTimeout,
                    NetworkError,
                )
            ),
            reraise=True,
        )
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    "network_error_retry_exhausted",
                    function=func.__name__,
                    error=str(e),
                    max_attempts=max_attempts,
                )
                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            @retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_random_exponential(multiplier=1, min=min_wait, max=max_wait),
                retry=retry_if_exception_type(
                    (
                        httpx.NetworkError,
                        httpx.TimeoutException,
                        NetworkError,
                    )
                ),
                reraise=True,
            )
            def _inner() -> Any:
                return func(*args, **kwargs)

            return _inner()

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def retry_on_server_error(
    max_attempts: int = 3, min_wait: int = 1, max_wait: int = 10
) -> Callable[[F], F]:
    """Retry decorator for server errors (5xx).

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: F) -> F:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type((ServerError, httpx.HTTPStatusError)),
            reraise=True,
        )
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                # Only retry on 5xx errors
                if 500 <= e.response.status_code < 600:
                    logger.warning(
                        "server_error_retrying",
                        function=func.__name__,
                        status_code=e.response.status_code,
                    )
                    raise
                else:
                    # Don't retry client errors
                    raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            @retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
                retry=retry_if_exception_type(ServerError),
                reraise=True,
            )
            def _inner() -> Any:
                return func(*args, **kwargs)

            return _inner()

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def retry_with_backoff(
    max_attempts: int = 5,
    min_wait: int = 2,
    max_wait: int = 60,
    retry_on_exceptions: tuple = (NetworkError, ServerError, RateLimitError),
) -> Callable[[F], F]:
    """General retry decorator with exponential backoff and jitter.

    This is the most commonly used retry decorator, handling network errors,
    server errors, and rate limits.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        retry_on_exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            async for attempt_obj in AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_random_exponential(multiplier=1, min=min_wait, max=max_wait),
                retry=retry_if_exception_type(retry_on_exceptions),
                reraise=True,
            ):
                with attempt_obj:
                    attempt = attempt_obj.retry_state.attempt_number
                    if attempt > 1:
                        logger.info(
                            "retry_attempt",
                            function=func.__name__,
                            attempt=attempt,
                            max_attempts=max_attempts,
                        )
                    return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            @retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_random_exponential(multiplier=1, min=min_wait, max=max_wait),
                retry=retry_if_exception_type(retry_on_exceptions),
                reraise=True,
            )
            def _inner() -> Any:
                return func(*args, **kwargs)

            return _inner()

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


async def retry_with_rate_limit_handling(
    coro: Callable[..., Any],
    max_attempts: int = 5,
    min_wait: int = 2,
    max_wait: int = 120,
) -> Any:
    """Retry a coroutine with special handling for rate limits.

    This function respects the Retry-After header from 429 responses.

    Args:
        coro: Coroutine to retry
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds

    Returns:
        Result of the coroutine

    Raises:
        RateLimitError: If all retry attempts are exhausted
    """
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        try:
            return await coro()
        except RateLimitError as e:
            if attempt >= max_attempts:
                logger.error(
                    "rate_limit_retry_exhausted",
                    attempt=attempt,
                    max_attempts=max_attempts,
                )
                raise

            # Use Retry-After header if available, otherwise exponential backoff
            wait_time = e.retry_after if e.retry_after else min(min_wait * (2**attempt), max_wait)

            logger.warning(
                "rate_limit_retrying",
                attempt=attempt,
                max_attempts=max_attempts,
                wait_seconds=wait_time,
            )

            await asyncio.sleep(wait_time)
        except Exception:
            raise

    raise RateLimitError("Rate limit retry exhausted")


def retry_on_gateway_error(
    max_attempts: int = 3,
    backoff_base: float = 2.0,
) -> Callable[[F], F]:
    """Retry decorator for AAP 2.6 Platform Gateway errors (502/503/504).

    The Platform Gateway can become overloaded and return gateway errors under
    high concurrency. This decorator implements exponential backoff retry logic
    specifically for these transient errors.

    Gateway errors that trigger retry:
    - 502 Bad Gateway: Gateway received invalid response from upstream
    - 503 Service Unavailable: Gateway temporarily unavailable
    - 504 Gateway Timeout: Gateway timeout waiting for upstream

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        backoff_base: Exponential backoff base multiplier (default: 2.0)
                     Delay = backoff_base^attempt seconds
                     Example with base=2.0: 2s, 4s, 8s

    Returns:
        Decorated function with gateway error retry logic

    Example:
        >>> @retry_on_gateway_error(max_attempts=3, backoff_base=2.0)
        >>> async def cancel_job(job_id: int):
        >>>     await client.post(f"jobs/{job_id}/cancel/")
    """

    def is_gateway_error(exc: Exception) -> bool:
        """Check if exception is a gateway error (502/503/504)."""
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in (502, 503, 504)
        # Also check string representation for wrapped errors
        error_str = str(exc)
        return any(code in error_str for code in ("502", "503", "504"))

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Async wrapper with gateway error retry logic."""
            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if not is_gateway_error(e):
                        # Not a gateway error - don't retry
                        raise

                    last_exception = e

                    if attempt >= max_attempts:
                        # Final attempt failed
                        logger.error(
                            "gateway_error_retry_exhausted",
                            function=func.__name__,
                            error=str(e),
                            attempts=attempt,
                        )
                        raise

                    # Calculate exponential backoff delay
                    delay = backoff_base**attempt
                    logger.warning(
                        "gateway_error_retrying",
                        function=func.__name__,
                        error=str(e),
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay_seconds=delay,
                    )

                    await asyncio.sleep(delay)

            # Should never reach here, but satisfy type checker
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry loop exit")

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Sync wrapper with gateway error retry logic."""
            import time

            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if not is_gateway_error(e):
                        raise

                    last_exception = e

                    if attempt >= max_attempts:
                        logger.error(
                            "gateway_error_retry_exhausted",
                            function=func.__name__,
                            error=str(e),
                            attempts=attempt,
                        )
                        raise

                    delay = backoff_base**attempt
                    logger.warning(
                        "gateway_error_retrying",
                        function=func.__name__,
                        error=str(e),
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay_seconds=delay,
                    )

                    time.sleep(delay)

            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry loop exit")

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


# Pre-configured decorators for common use cases
retry_api_call = retry_with_backoff(max_attempts=5, min_wait=2, max_wait=60)
retry_api_call_short = retry_with_backoff(max_attempts=3, min_wait=1, max_wait=10)
retry_network_only = retry_on_network_error(max_attempts=5, min_wait=2, max_wait=60)
retry_server_only = retry_on_server_error(max_attempts=3, min_wait=1, max_wait=10)
