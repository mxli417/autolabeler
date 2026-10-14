from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

EMAIL = "erika.muster@example.test"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._send({"status": "ok"})
            return
        self._send({"error": "not found"}, status=404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length))
        text = request.get("text", "")
        role = os.environ["ROLE"]

        if role == "analyzer" and self.path == "/analyze":
            start = text.index(EMAIL)
            self._send([{"start": start, "end": start + len(EMAIL), "entity_type": "EMAIL_ADDRESS", "score": 0.99}])
            return
        if role == "anonymizer" and self.path == "/anonymize":
            self._send({"text": text.replace(EMAIL, "<EMAIL_ADDRESS>")})
            return
        self._send({"error": "not found"}, status=404)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "3000"))), Handler).serve_forever()
