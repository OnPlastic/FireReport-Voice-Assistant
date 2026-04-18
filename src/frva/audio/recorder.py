"""Hilfsfunktionen für Audio-Dateien im FRVA-MVP."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4


AUDIO_INPUT_DIR = Path("data/input/audio")
AUDIO_INPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_uploaded_audio_path(suffix: str = ".wav") -> Path:
    """Erzeugt einen eindeutigen Zielpfad für eine hochgeladene Audiodatei."""
    return AUDIO_INPUT_DIR / f"audio_{uuid4().hex}{suffix}"