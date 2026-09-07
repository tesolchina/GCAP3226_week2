#!/usr/bin/env python3
"""server.py — Week 2 Lab GUI server (Python standard library only).

Run inside the Codespace (or anywhere with python3 + the week-2 requirements):

    python3 lab/server.py          # then open http://localhost:8123

Routes
    GET  /                    static GUI (static/index.html)
    GET  /app.js, /style.css  static assets
    GET  /api/health          {"ok": true, "service": "week2-lab", ...}
    POST /api/analyze         body = raw CSV text (or empty body -> demo week2.csv)
                              -> JSON from analyze.analyse(): charts (base64 PNG),
                                 the exact code that ran, workflow, pseudocode.

Design: simplified from the DataGuru recipe-runner pattern
(tesolchina/dataguru — zero-dep server, deterministic Python analysis, JSON
out), adapted to pure Python so students need no Node install.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
DEMO_CANDIDATES = [HERE / "data" / "week2.csv", HERE.parent / "week2.csv"]

MAX_BODY = 12 * 1024 * 1024  # 12 MB (same ceiling as DataGuru uploads)

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".csv": "text/csv; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".json": "application/json; charset=utf-8",
}


def find_demo() -> Path:
    for p in DEMO_CANDIDATES:
        if p.is_file():
            return p
    raise FileNotFoundError("week2.csv demo not found — run from the repo root or lab/.")


class Handler(BaseHTTPRequestHandler):
    server_version = "Week2Lab/0.1"

    # -- helpers ---------------------------------------------------------

    def _send(self, status: int, body: bytes, content_type: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _static(self, rel: str) -> None:
        # Safe path join (no directory escape), mirroring DataGuru's static guard.
        try:
            file_path = (STATIC / rel.lstrip("/")).resolve()
            file_path.relative_to(STATIC)
        except ValueError:
            return self._json(404, {"error": "Not found"})
        if not file_path.is_file():
            return self._json(404, {"error": "Not found"})
        body = file_path.read_bytes()
        self._send(200, body, MIME.get(file_path.suffix.lower(), "application/octet-stream"))

    def log_message(self, fmt, *args):  # quieter logs
        sys.stderr.write("week2-lab: %s\n" % (fmt % args))

    # -- CORS for local tooling (same as DataGuru) -----------------------
    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    # -- GET -------------------------------------------------------------
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            return self._json(200, {
                "ok": True,
                "service": "week2-lab",
                "version": "0.1.0",
                "demo": str(find_demo().name),
            })
        if path in ("/", "/index.html"):
            return self._static("index.html")
        if path in ("/app.js", "/style.css"):
            return self._static(path.lstrip("/"))
        return self._json(404, {"error": "Not found"})

    # -- POST ------------------------------------------------------------
    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/analyze":
            return self._analyze()
        return self._json(404, {"error": "Not found"})

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError("File too large (max 12 MB)")
        return self.rfile.read(length) if length else b""

    def _analyze(self) -> None:
        try:
            import analyze  # local import keeps static/health usable without pandas
        except ImportError as exc:
            return self._json(500, {
                "ok": False,
                "error": f"Analysis libraries not installed: {exc} — run: pip install -r requirements.txt",
            })

        try:
            raw = self._read_body()
        except ValueError as exc:
            return self._json(413, {"ok": False, "error": str(exc)})

        try:
            if raw.strip():
                with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as fh:
                    fh.write(raw)
                    tmp = fh.name
                result = analyze.analyse(tmp, filename="uploaded.csv")
                os.unlink(tmp)
            else:
                result = analyze.analyse(str(find_demo()), filename=find_demo().name)
            self._json(200, result)
        except Exception as exc:  # noqa: BLE001
            self._json(500, {"ok": False, "error": f"Server error: {exc}"})


def main() -> None:
    # Import once in the main thread so matplotlib picks the Agg backend before
    # any worker thread draws a chart (avoids GUI-backend warnings in logs).
    try:
        import analyze  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        print(f"week2-lab: warning — analyze import failed ({exc}); demo/upload will error", flush=True)
    port = int(os.environ.get("PORT", "8123"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Week 2 Lab GUI → http://localhost:{port}   (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
