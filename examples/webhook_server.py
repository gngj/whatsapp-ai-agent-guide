#!/usr/bin/env python3
"""Minimal WhatsApp Cloud API webhook (standard library only).

- GET  : answers Meta's verification handshake (hub.challenge).
- POST : optionally validates X-Hub-Signature-256 with your app secret,
         appends each inbound message / status to a JSONL file, and returns 200.

Configuration (environment variables):
  VERIFY_TOKEN_FILE  path to a file holding your verify token   (or VERIFY_TOKEN)
  APP_SECRET_FILE    path to a file holding your app secret     (optional, or APP_SECRET)
  WEBHOOK_PORT       default 8787
  EVENTS_FILE        default ./events.jsonl

Binds to 127.0.0.1. Put a tunnel, reverse proxy or load balancer with real TLS in front.
Query strings are never logged, so the verify token does not end up in logs.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


def read_secret(name: str, required: bool) -> str | None:
    path = os.environ.get(f"{name}_FILE")
    if path and Path(path).is_file():
        return Path(path).read_text().strip()
    value = os.environ.get(name)
    if value:
        return value.strip()
    if required:
        sys.exit(f"{name} (or {name}_FILE) is required")
    return None


VERIFY_TOKEN = read_secret("VERIFY_TOKEN", required=True)
APP_SECRET = read_secret("APP_SECRET", required=False)
PORT = int(os.environ.get("WEBHOOK_PORT", "8787"))
EVENTS_FILE = Path(os.environ.get("EVENTS_FILE", "events.jsonl"))
_seen: set[str] = set()  # in-memory dedup; use a real store in production


def extract(body: dict) -> list[dict]:
    """Flatten a Cloud API payload into inbound messages and delivery statuses."""
    out: list[dict] = []
    for entry in body.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            names = {c.get("wa_id"): (c.get("profile") or {}).get("name") for c in value.get("contacts") or []}
            for m in value.get("messages") or []:
                item = {
                    "kind": "message",
                    "id": m.get("id"),
                    "from": m.get("from"),
                    "name": names.get(m.get("from")),
                    "timestamp": m.get("timestamp"),
                    "type": m.get("type"),
                    "phone_number_id": (value.get("metadata") or {}).get("phone_number_id"),
                }
                if m.get("type") == "text":
                    item["text"] = (m.get("text") or {}).get("body", "")
                media = m.get(m.get("type") or "") if isinstance(m.get(m.get("type") or ""), dict) else None
                if media and "id" in media:
                    item["media_id"] = media["id"]
                    item["mime_type"] = media.get("mime_type")
                    item["voice"] = media.get("voice", False)
                out.append(item)
            for s in value.get("statuses") or []:
                out.append({
                    "kind": "status",
                    "id": s.get("id"),
                    "status": s.get("status"),
                    "recipient": s.get("recipient_id"),
                    "timestamp": s.get("timestamp"),
                    "errors": s.get("errors"),
                })
    return out


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:  # log method + path only, never the query
        sys.stderr.write(f"{self.command} {urlparse(self.path).path} -> {args[1] if len(args) > 1 else ''}\n")

    def _reply(self, code: int, body: bytes = b"", ctype: str = "text/plain; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self) -> None:
        q = parse_qs(urlparse(self.path).query)
        mode = (q.get("hub.mode") or [""])[0]
        token = (q.get("hub.verify_token") or [""])[0]
        challenge = (q.get("hub.challenge") or [None])[0]
        if mode == "subscribe" and challenge is not None and hmac.compare_digest(token, VERIFY_TOKEN):
            self._reply(200, challenge.encode())
        else:
            self._reply(403)

    def do_POST(self) -> None:
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if APP_SECRET:
            expected = "sha256=" + hmac.new(APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, self.headers.get("X-Hub-Signature-256", "")):
                self._reply(401)
                return
        self._reply(200)  # acknowledge first; do slow work elsewhere
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return
        received_at = datetime.now(timezone.utc).isoformat()
        with EVENTS_FILE.open("a", encoding="utf-8") as f:
            for item in extract(body):
                key = f"{item['kind']}:{item.get('id')}:{item.get('status', '')}"
                if key in _seen:
                    continue
                _seen.add(key)
                item["received_at"] = received_at
                f.write(json.dumps(item, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    print(f"listening on http://127.0.0.1:{PORT}  (signature check: {'on' if APP_SECRET else 'off'})", file=sys.stderr)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
