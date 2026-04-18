"""Whisper-Wrapper für den FRVA-MVP.

Diese Schicht kapselt die Nutzung von Whisper für Audio-Dateien.
Noch keine Live-Aufnahme, noch keine Dialogkopplung.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import whisper


DEFAULT_MODEL_NAME = "base"


def load_whisper_model(model_name: str = DEFAULT_MODEL_NAME) -> Any:
    """Lädt ein Whisper-Modell über die Whisper-Bibliothek."""
    return whisper.load_model(model_name)


def transcribe_audio_file(
    audio_path: str | Path,
    model_name: str = DEFAULT_MODEL_NAME,
    language: str = "de",
) -> str:
    """Transkribiert eine Audiodatei und gibt den erkannten Text zurück.

    Args:
        audio_path:
            Pfad zur Audiodatei.
        model_name:
            Name des Whisper-Modells.
        language:
            Sprachhinweis für Whisper, z. B. "de".

    Returns:
        Das erkannte Transkript als String.

    Raises:
        FileNotFoundError:
            Wenn die Audiodatei nicht existiert.
        ValueError:
            Wenn Whisper keinen verwertbaren Text liefert.
    """
    path = Path(audio_path)

    if not path.exists():
        raise FileNotFoundError(f"Audiodatei nicht gefunden: {path}")

    model = load_whisper_model(model_name=model_name)
    result = model.transcribe(str(path), language=language)

    text = result.get("text", "")
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("Whisper hat kein verwertbares Transkript geliefert.")

    return cleaned_text