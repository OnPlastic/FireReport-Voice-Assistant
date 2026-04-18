"""Audio-basierte Turn-Verarbeitung für den FRVA-MVP."""

from __future__ import annotations

from pathlib import Path

from frva.asr.whisper_asr import transcribe_audio_file
from frva.dialog.manager import process_turn
from frva.dialog.state import DialogSession
from frva.extraction.basic_extractor import extract_updates
from frva.model.report_schema import FieldUpdate


def process_audio_turn(
    session: DialogSession,
    audio_path: str | Path,
    *,
    use_extractor: bool = True,
    updates: dict[str, FieldUpdate[object]] | None = None,
    model_name: str = "base",
    language: str = "de",
) -> tuple[str, str | None]:
    """Verarbeitet einen Dialogschritt aus einer Audiodatei.

    Ablauf:
    1. Audiodatei mit Whisper transkribieren
    2. optional einfache Updates heuristisch extrahieren
    3. bestehenden Text-Turn-Prozessor verwenden

    Args:
        session:
            Aktuelle Dialogsitzung.
        audio_path:
            Pfad zur Audiodatei.
        use_extractor:
            Wenn True und keine Updates übergeben wurden, wird der Basic Extractor genutzt.
        updates:
            Optional bereits vorbereitete Updates. Diese haben Vorrang vor dem Extractor.
        model_name:
            Whisper-Modellname.
        language:
            Sprachhinweis für Whisper.

    Returns:
        Tuple aus:
        - transkribiertem Text
        - nächster Frage oder None
    """
    transcript = transcribe_audio_file(
        audio_path=audio_path,
        model_name=model_name,
        language=language,
    )

    final_updates: dict[str, FieldUpdate[object]]

    if updates is not None:
        final_updates = updates
    elif use_extractor:
        final_updates = extract_updates(transcript)
    else:
        final_updates = {}

    next_question = process_turn(
        session=session,
        user_transcript=transcript,
        updates=final_updates,
    )

    return transcript, next_question