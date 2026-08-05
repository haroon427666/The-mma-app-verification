"""Tests for the ETag / conditional-GET helper (src/api/etag.py)."""

import json

from fastapi import Request

from src.api.etag import conditional_json_response, etag_for


def test_etag_for_is_deterministic():
    payload = {"id": "abc", "nested": {"b": 2, "a": 1}, "date": None}
    assert etag_for(payload) == etag_for(payload)


def test_etag_for_changes_with_payload():
    assert etag_for({"a": 1}) != etag_for({"a": 2})


def test_etag_for_key_order_independent():
    assert etag_for({"a": 1, "b": 2}) == etag_for({"b": 2, "a": 1})


def test_conditional_returns_200_with_headers():
    resp = conditional_json_response(
        _req(), {"id": "event-1", "name": "UFC"}, max_age=300
    )
    assert resp.status_code == 200
    etag = resp.headers["ETag"]
    assert etag.startswith('"')
    assert resp.headers["Cache-Control"] == "public, max-age=300"
    body = json.loads(resp.body)
    assert body["name"] == "UFC"


def test_conditional_returns_304_on_match():
    payload = {"id": "event-1", "name": "UFC"}
    etag = f'"{etag_for(payload)}"'
    resp = conditional_json_response(_req(if_none_match=etag), payload=payload)
    assert resp.status_code == 304
    assert resp.headers["ETag"] == etag
    assert b"{" not in resp.body


def test_conditional_returns_200_on_mismatch():
    payload = {"id": "event-1"}
    resp = conditional_json_response(_req(if_none_match='"wrong-etag"'), payload=payload)
    assert resp.status_code == 200


def _req(if_none_match: str | None = None) -> Request:
    headers = []
    if if_none_match:
        headers = [(b"if-none-match", if_none_match.encode())]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": headers,
        "scheme": "http",
        "server": ("test", 80),
        "client": ("127.0.0.1", 1234),
        "query_string": b"",
    }
    return Request(scope)