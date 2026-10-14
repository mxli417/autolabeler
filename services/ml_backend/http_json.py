from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen


def post_json(url: str, payload: dict[str, Any], timeout: float, headers: dict[str, str] | None = None) -> Any:
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - endpoints are explicit operator configuration
        return json.load(response)
