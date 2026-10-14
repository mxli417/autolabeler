from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, {"status": "ok"})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/v1/responses":
            self._send(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length))
        content = request.get("input", [{}])[0].get("content", [])
        text_parts = [item.get("text", "") for item in content if item.get("type") == "input_text"]
        image_parts = [item for item in content if item.get("type") == "input_image"]
        joined_text = "\n".join(text_parts)
        checks = {
            "uses_responses_endpoint": True,
            "has_redacted_email": "<EMAIL_ADDRESS>" in joined_text,
            "original_email_absent": "erika.muster@example.test" not in joined_text,
            "has_image": bool(image_parts),
            "store_disabled": request.get("store") is False,
        }
        if not all(checks.values()):
            self._send(422, {"error": "e2e request validation failed", "checks": checks})
            return

        self._send(
            200,
            {
                "id": "resp_e2e",
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "model": request.get("model", "e2e-multimodal"),
                "output": [
                    {
                        "id": "msg_e2e",
                        "type": "message",
                        "status": "completed",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"label":"relevant","confidence":0.91}',
                                "annotations": [],
                            }
                        ],
                    }
                ],
                "parallel_tool_calls": True,
                "tool_choice": "auto",
                "tools": [],
            },
        )

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "4000"))), Handler).serve_forever()
