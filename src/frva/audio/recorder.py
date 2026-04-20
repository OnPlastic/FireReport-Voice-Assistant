"""Hilfsfunktionen für aufgezeichnete Audio-Dateien im FRVA-MVP."""

from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4


AUDIO_INPUT_DIR = Path("data/input/audio")
AUDIO_INPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_recorded_audio_path(suffix: str = ".webm") -> Path:
    """Erzeugt einen eindeutigen Zielpfad für eine Browser-Audioaufnahme."""
    return AUDIO_INPUT_DIR / f"audio_{uuid4().hex}{suffix}"


def save_data_url_audio(data_url: str, target_path: str | Path) -> Path:
    """Speichert ein Audio-Data-URL-Objekt als Binärdatei."""
    if not data_url.startswith("data:"):
        raise ValueError("Ungültige Data-URL für Audio.")

    try:
        _, encoded = data_url.split(",", 1)
    except ValueError as exc:
        raise ValueError("Data-URL konnte nicht getrennt werden.") from exc

    output = Path(target_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(base64.b64decode(encoded))

    return output