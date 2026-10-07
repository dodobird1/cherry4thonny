"""Talk to a Sakura host. Either sakura-trunk or full Sakura can run the bridge."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from cherry.paths import bridge_file


class BridgeUnavailable(Exception):
    pass


def ask(text: str, *, timeout: float = 50) -> str:
    path = bridge_file()
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        port = int(record["port"])
        token = str(record["token"])
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise BridgeUnavailable("bridge file missing") from error
    payload = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/turn",
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError) as error:
        raise BridgeUnavailable("bridge request failed") from error
    if not isinstance(body, dict) or not body.get("ok"):
        raise BridgeUnavailable(str(body.get("error") if isinstance(body, dict) else "bad reply"))
    reply = body.get("reply")
    if not isinstance(reply, str) or not reply.strip():
        raise BridgeUnavailable("empty reply")
    return reply
