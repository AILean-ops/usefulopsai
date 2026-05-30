#!/usr/bin/env python3
"""Serve the private UsefulOps dashboard on localhost only."""

from __future__ import annotations

import json
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_dashboard import DASHBOARD_HTML, DASHBOARD_JSON, build_dashboard  # noqa: E402

HOST = "127.0.0.1"
PORT = int(os.environ.get("USEFULOPS_DASHBOARD_PORT", "8766"))


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "UsefulOpsDashboard/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[dashboard] {self.address_string()} - {format % args}")

    def _loopback_only(self) -> bool:
        return self.client_address[0] in {"127.0.0.1", "::1"}

    def _send(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
        self.send_response(status.value)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        self._send(status, "application/json; charset=utf-8", json.dumps(payload, indent=2, sort_keys=True).encode("utf-8"))

    def _forbidden_if_remote(self) -> bool:
        if self._loopback_only():
            return False
        self._json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "loopback clients only"})
        return True

    def do_GET(self) -> None:
        if self._forbidden_if_remote():
            return

        path = urlparse(self.path).path
        if path in {"/", "/dashboard"}:
            if not DASHBOARD_HTML.exists():
                build_dashboard()
            self._send(HTTPStatus.OK, "text/html; charset=utf-8", DASHBOARD_HTML.read_bytes())
            return

        if path == "/api/dashboard":
            if not DASHBOARD_JSON.exists():
                build_dashboard()
            self._send(HTTPStatus.OK, "application/json; charset=utf-8", DASHBOARD_JSON.read_bytes())
            return

        if path == "/health":
            self._json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "bind": HOST,
                    "port": PORT,
                    "dashboard": str(DASHBOARD_HTML),
                    "public": False,
                },
            )
            return

        self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        if self._forbidden_if_remote():
            return

        path = urlparse(self.path).path
        if path == "/api/refresh":
            result = build_dashboard()
            self._json(HTTPStatus.OK, result)
            return

        self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})


def main() -> int:
    if not DASHBOARD_HTML.exists() or not DASHBOARD_JSON.exists():
        build_dashboard()

    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f"UsefulOps private dashboard listening at http://localhost:{PORT}")
    print("Bound to 127.0.0.1 only. Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping UsefulOps private dashboard.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
