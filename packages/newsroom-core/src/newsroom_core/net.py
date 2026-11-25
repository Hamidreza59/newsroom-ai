import truststore

truststore.inject_into_ssl()

import httpx

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) newsroom-ai/0.1"


def http_client(timeout: float = 20.0) -> httpx.Client:
    return httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}, follow_redirects=True)


def async_http_client(timeout: float = 120.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=timeout, headers={"User-Agent": USER_AGENT}, follow_redirects=True
    )
