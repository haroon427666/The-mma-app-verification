"""ETag / conditional-GET helpers for cacheable endpoints.

Produces stable ETags from response payloads so CDNs and browsers can send
``If-None-Match`` and get a cheap ``304 Not Modified`` when nothing changed.
"""

import hashlib
import json
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse, Response


def etag_for(payload: Any) -> str:
    """Stable content hash for a JSON-serializable payload."""
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def conditional_json_response(
    request: Request,
    payload: Any,
    max_age: int = 300,
) -> Response:
    """Return 304 when ``If-None-Match`` matches, else 200 with ETag + Cache-Control."""
    etag = f'"{etag_for(payload)}"'
    headers = {"ETag": etag, "Cache-Control": f"public, max-age={max_age}"}
    if request.headers.get("If-None-Match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return JSONResponse(payload, headers=headers)
