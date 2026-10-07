"""Where the local bridge file lives. The Sakura plugin writes the same path."""

from __future__ import annotations

import os
from pathlib import Path


def bridge_file() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "cherry" / "bridge.json"
