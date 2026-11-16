#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "pydantic>=2", "pillow>=11", "pillow-heif"]
# ///
"""Resale dashboard server — a thin HTTP shim over resale_store.

The browser needs HTTP; that is the only reason this process exists. It owns
no schema, no whitelist and no write logic: `resale_store` is the single write
path, and this file does not import `yaml` at all.

Usage: uv run server.py → http://127.0.0.1:8377   (reads $RESALE_BASE, default ~/resale)
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

import resale_store as rs  # noqa: E402

PORT = 8377


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False).encode())

    # ---------------- GET ----------------

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send(
                200, (BASE / "index.html").read_bytes(), "text/html; charset=utf-8"
            )
        elif self.path in ("/api/inventory", "/api/inventory?all=1"):
            try:
                rows = rs.load_all(archived=self.path.endswith("all=1"))
            except rs.Invalid as e:
                # Never render a partial inventory: a skipped bad file would be
                # an item silently missing from the cockpit.
                self._json(
                    500, {"error": "inventory does not validate", "errors": e.errors}
                )
                return
            self._json(
                200,
                {
                    "items": [rs.view(i) | {"rev": r} for i, r in rows],
                    "schema": _enums(),
                },
            )
        elif self.path == "/api/tax":
            # The tax cards show exactly what `resale_store.py tax` computes.
            from datetime import date

            try:
                self._json(200, rs.tax_report(date.today().year))
            except rs.Invalid as e:
                self._json(500, {"error": "tax report failed", "errors": e.errors})
        elif self.path == "/api/schema":
            self._json(200, rs.Item.model_json_schema())
        else:
            self._json(404, {"error": "not found"})

    # ---------------- POST ----------------

    def do_POST(self) -> None:
        if not self.path.startswith("/api/item/"):
            self._json(404, {"error": "not found"})
            return
        rest = self.path[len("/api/item/") :]
        uid, _, action = rest.partition("/")
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        rev = body.get("rev")
        if action == "sold":
            patch = {"disposition": "sold", "sale": body.get("sale", {})}
        else:
            patch = body.get("patch", {})
        try:
            item, new_rev = rs.update(uid, patch, expected_rev=rev)
        except rs.Conflict as e:
            self._json(409, {"error": str(e)})
        except rs.Invalid as e:
            self._json(422, {"errors": e.errors})
        except rs.NotFound as e:
            self._json(404, {"error": str(e)})
        else:
            self._json(200, {"ok": True, "item": rs.view(item) | {"rev": new_rev}})

    def log_message(self, fmt: str, *args) -> None:  # quiet
        pass


def _enums() -> dict:
    """Enum choices for the UI's <select>s — one source, the model."""
    from typing import get_args

    return {
        "condition": list(get_args(rs.Condition)),
        "category": list(get_args(rs.Category)),
        "sale_platform": list(get_args(rs.SalePlatform)),
        "acq_source": ["order_page", "receipt", "msrp", "seller", "estimate"],
        "acq_date_basis": [
            "order",
            "receipt",
            "memory",
            "release_date",
            "estimate",
            "unknown",
        ],
        "sale_date_basis": ["exact", "approx", "unknown"],
        "confidence": ["high", "medium", "low"],
        "disposition": list(get_args(rs.Disposition)),
    }


if __name__ == "__main__":
    print(f"Resale dashboard → http://127.0.0.1:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
