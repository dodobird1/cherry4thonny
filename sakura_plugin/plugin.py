"""Localhost bridge. Install this folder into either host's plugins/user directory."""

from __future__ import annotations

import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def bridge_file() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "cherry" / "bridge.json"


class CherryBridge:
    def __init__(self) -> None:
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._token = ""

    def setup(self, context) -> None:
        self._conversation = context.get("sakura.host.conversation")
        self._logger = context.get("sakura.host.logging")
        context.effect(self.close)
        self._token = secrets.token_urlsafe(24)
        handler = _handler(self._token, self._reply)
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, name="cherry-bridge", daemon=True)
        self._thread.start()
        path = bridge_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"port": self._server.server_address[1], "token": self._token}),
            encoding="utf-8",
        )
        try:
            path.chmod(0o600)
        except OSError:
            pass
        self._logger.info("樱桃桥已打开", fields={"port": self._server.server_address[1]})

    def close(self) -> None:
        server = self._server
        self._server = None
        if server is not None:
            server.shutdown()
        path = bridge_file()
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            record = None
        if isinstance(record, dict) and record.get("token") == self._token:
            path.unlink(missing_ok=True)

    def _reply(self, text: str) -> str:
        job = self._conversation.begin("", text, None)
        job_id = job["jobId"]
        for _ in range(90):
            state = self._conversation.poll(job_id)
            if state.get("status") == "completed":
                result = state.get("result") or {}
                reply = result.get("reply") or result.get("reply_raw") or ""
                if not isinstance(reply, str) or not reply.strip():
                    raise RuntimeError("empty model reply")
                return reply
            if state.get("status") not in (None, "running"):
                raise RuntimeError(state.get("status") or "conversation failed")
            time.sleep(0.5)
        self._conversation.cancel(job_id)
        raise RuntimeError("conversation timed out")


def _handler(token: str, reply):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/turn" or self.headers.get("Authorization") != f"Bearer {token}":
                self._send(403, {"ok": False, "error": "forbidden"})
                return
            length = int(self.headers.get("Content-Length") or "0")
            if length <= 0 or length > 100_000:
                self._send(400, {"ok": False, "error": "bad length"})
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                text = payload["text"]
                if not isinstance(text, str) or not text.strip():
                    raise ValueError("text")
                body = {"ok": True, "reply": reply(text)}
                self._send(200, body)
            except Exception as error:
                self._send(502, {"ok": False, "error": str(error)})

        def log_message(self, format: str, *args) -> None:
            return

        def _send(self, status: int, body: dict) -> None:
            raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    return Handler
