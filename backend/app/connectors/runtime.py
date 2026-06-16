"""Runtime connector configuration.

Stores per-connector *mode* overrides ("mock" | "live") in a small JSON file under
the data directory, so the Setup page can switch a connector between bundled sample
data and live cloud APIs without editing ``.env`` or restarting the server.

Only non-secret settings are persisted here. Credentials always come from the
environment (``.env`` / ``az login`` / AWS profile) and are never written to disk.
"""
from __future__ import annotations

import json
import os
import threading
from typing import Dict

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

_LOCK = threading.Lock()
_VALID_MODES = {"mock", "live"}


def _config_path() -> str:
    # chroma_persist_dir is e.g. "./.data/chroma" -> data dir is its parent.
    data_dir = os.path.dirname(settings.chroma_persist_dir.rstrip("/\\")) or ".data"
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "runtime.json")


def _read() -> Dict:
    path = _config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # corrupt file -> ignore overrides
        return {}


def _write(data: Dict) -> None:
    path = _config_path()
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp, path)


def get_mode(name: str) -> str:
    """Effective mode for a connector: runtime override, else env default."""
    overrides = _read().get("modes", {})
    mode = overrides.get(name) or settings.connector_mode(name)
    return mode if mode in _VALID_MODES else "mock"


def set_mode(name: str, mode: str) -> str:
    if mode not in _VALID_MODES:
        raise ValueError(f"Invalid mode '{mode}'. Use one of {sorted(_VALID_MODES)}.")
    with _LOCK:
        data = _read()
        data.setdefault("modes", {})[name] = mode
        _write(data)
    logger.info("Connector '%s' mode set to '%s'.", name, mode)
    return mode


def all_modes(names: list[str]) -> Dict[str, str]:
    return {n: get_mode(n) for n in names}
