from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "morning_prayer.json"
TEMPLATE_PATH = BASE_DIR / "templates" / "index.html"
STATIC_DIR = BASE_DIR / "static"


class AppHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        self._handle_request(send_body=True)

    def do_HEAD(self) -> None:
        self._handle_request(send_body=False)

    def _handle_request(self, send_body: bool) -> None:
        if self.path == "/":
            self._serve_index(send_body)
            return

        if self.path == "/api/morning-prayer":
            self._serve_dataset(send_body)
            return

        if self.path.startswith("/static/"):
            self.path = self.path.removeprefix("/static/")
            if send_body:
                return super().do_GET()
            return super().do_HEAD()

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def translate_path(self, path: str) -> str:
        if path.startswith("/"):
            path = path[1:]
        return str(STATIC_DIR / path)

    def _serve_index(self, send_body: bool) -> None:
        html = TEMPLATE_PATH.read_text(encoding="utf-8")
        payload = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if send_body:
            self.wfile.write(payload)

    def _serve_dataset(self, send_body: bool) -> None:
        dataset = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        payload = json.dumps(dataset).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if send_body:
            self.wfile.write(payload)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), AppHandler)
    print("Serving on http://0.0.0.0:8000")
    server.serve_forever()
