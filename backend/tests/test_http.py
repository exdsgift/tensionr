"""Retry helper: backoff, Retry-After and exhaustion behavior."""

import requests

from tensionr import http_client
from tensionr.http_client import request_with_retry


class FakeResponse:
    def __init__(self, status_code: int, headers: dict | None = None):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = ""


def test_returns_first_success(monkeypatch):
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append(url)
        return FakeResponse(200)

    monkeypatch.setattr(requests, "request", fake_request)
    resp = request_with_retry("GET", "http://x")
    assert resp.status_code == 200
    assert len(calls) == 1


def test_retries_on_503_honoring_retry_after(monkeypatch):
    sleeps = []
    monkeypatch.setattr(http_client.time, "sleep", sleeps.append)
    responses = [FakeResponse(503, {"Retry-After": "7"}), FakeResponse(200)]
    monkeypatch.setattr(requests, "request", lambda *a, **k: responses.pop(0))

    resp = request_with_retry("GET", "http://x")
    assert resp.status_code == 200
    assert sleeps == [7.0]


def test_exponential_backoff_and_exhaustion(monkeypatch):
    sleeps = []
    monkeypatch.setattr(http_client.time, "sleep", sleeps.append)
    monkeypatch.setattr(requests, "request", lambda *a, **k: FakeResponse(503))

    assert request_with_retry("GET", "http://x", retries=3, base_delay=1.0) is None
    assert sleeps == [1.0, 2.0, 4.0]


def test_non_retryable_status_returned_immediately(monkeypatch):
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append(url)
        return FakeResponse(404)

    monkeypatch.setattr(requests, "request", fake_request)
    resp = request_with_retry("GET", "http://x")
    assert resp.status_code == 404
    assert len(calls) == 1


def test_connection_errors_retried_then_none(monkeypatch):
    monkeypatch.setattr(http_client.time, "sleep", lambda _: None)

    def fake_request(method, url, **kwargs):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(requests, "request", fake_request)
    assert request_with_retry("GET", "http://x", retries=2) is None
