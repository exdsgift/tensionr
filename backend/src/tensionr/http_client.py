"""Single HTTP helper with retries, exponential backoff and Retry-After support."""

import logging
import time

import requests

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def request_with_retry(
    method: str,
    url: str,
    *,
    retries: int = 3,
    base_delay: float = 1.0,
    timeout: float = 15,
    **kwargs,
) -> requests.Response | None:
    """Issue an HTTP request, retrying transient failures.

    Returns the successful (or non-retryable) response, or None once retries
    are exhausted. Callers degrade gracefully on None.
    """
    for attempt in range(retries + 1):
        try:
            resp = requests.request(method, url, timeout=timeout, **kwargs)
        except requests.RequestException as e:
            if attempt == retries:
                logger.warning(
                    "request failed after %d retries: %s %s (%s)",
                    retries,
                    method,
                    url,
                    e,
                )
                return None
            time.sleep(base_delay * 2**attempt)
            continue

        if resp.status_code not in RETRYABLE_STATUS:
            return resp
        if attempt == retries:
            logger.warning("giving up on %s %s: HTTP %d", method, url, resp.status_code)
            return None

        delay = base_delay * 2**attempt
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                delay = min(float(retry_after), 30.0)
            except ValueError:
                pass
        time.sleep(delay)
    return None
