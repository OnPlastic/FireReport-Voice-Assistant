"""NiceGUI-Oberfläche für den FRVA-MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from uuid import uuid4

from nicegui import app, events, ui

from frva.audio.recorder import create_uploaded_audio_path
from frva.asr.whisper_asr import transcribe_audio_file
from frva.dialog.manager import process_turn, start_dialog
from frva.dialog.state import DialogSession
from frva.extraction.basic_extractor import extract_updates
from frva.report.formatter import format_report_summary
from frva.report.generator import generate_report_text
from frva.tts.piper_tts import synthesize_speech_to_file


Role = Literal["assistant", "user", "system"]

TTS_OUTPUT_DIR = Path("data/output/tts")
TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TTS_ROUTE = "/tts_audio"


@dataclass
class ChatMessage:
    """Ein sichtbarer Eintrag im Gesprächsverlauf."""
    role: Role
    text: str


@dataclass
class AppState:
    """UI-Zustand für die MVP-Oberfläche."""
    session: DialogSession | None = None
    status: str = "Bereit"
    messages: list[ChatMessage] = field(default_factory=list)
    summary: str = ""
    report: str = ""
    current_question: str = "-"
    recognized_answer: str = "-"
    tts_audio_url: str = ""


def append_message(state: AppState, role: Role, text: str) -> None:
    state.messages.append(ChatMessage(role=role, text=text))


def speak_text_to_url(text: str) -> str:
    """Erzeugt eine TTS-Datei und liefert die statische URL zurück."""
    output_path = TTS_OUTPUT_DIR / f"tts_{uuid4().hex}.wav"
    synthesize_speech_to_file(text, output_path)
    return f"{TTS_ROUTE}/{output_path.name}"


def set_assistant_question(
    state: AppState,
    question: str | None,
    *,
    speaker=speak_text_to_url,
) -> None:
    if question is None:
        state.current_question = "-"
        state.tts_audio_url = ""
        return

    state.current_question = question
    append_message(state, "assistant", question)

    audio_url = speaker(question)
    state.tts_audio_url = audio_url or ""


def start_ui_session(state: AppState) -> str | None:
    state.session = DialogSession()
    state.messages.clear()
    state.summary = ""
    state.report = ""
    state.recognized_answer = "-"
    state.tts_audio_url = ""
    state.status = "Dialog gestartet"

    first_question = start_dialog(state.session)

    if first_question is not None:
        set_assistant_question(state, first_question)
        state.status = "Warte auf Antwort"
    else:
        state.current_question = "-"
        state.status = "Bericht vollständig"

    return first_question


def handle_text_input(state: AppState, text: str) -> str | None:
    cleaned_text = text.strip()
    if not cleaned_text:
        return None

    if state.session is None:
        start_ui_session(state)

    assert state.session is not None

    state.recognized_answer = cleaned_text
    append_message(state, "user", cleaned_text)
    state.status = "Verarbeite Antwort"

    updates = extract_updates(cleaned_text)
    next_question = process_turn(
        session=state.session,
        user_transcript=cleaned_text,
        updates=updates,
    )

    if next_question is not None:
        set_assistant_question(state, next_question)
        state.status = "Habe erkannt"
        return next_question

    state.current_question = "-"
    state.tts_audio_url = ""
    state.summary = format_report_summary(state.session.report_state)
    state.report = generate_report_text(state.session.report_state)
    append_message(state, "system", "Danke, der Bericht ist vollständig.")
    state.status = "Bericht vollständig"
    return None


def build_ui() -> None:
    app.add_static_files(TTS_ROUTE, str(TTS_OUTPUT_DIR))

    state = AppState()

    with ui.column().classes("w-full max-w-5xl mx-auto p-4 gap-4 pb-24"):
        ui.label("FireReport Voice Assistant").classes("text-3xl font-bold")

        with ui.row().classes("w-full items-center gap-3"):
            start_button = ui.button("Dialog starten").classes("px-6 py-2")
            text_input = ui.input(
                label="Antwort eingeben",
                placeholder="Antwort hier eingeben und mit Enter senden ...",
            ).classes("w-full")

        with ui.row().classes("w-full items-center gap-3"):
            ui.label("Audio-Datei für Whisper hochladen").classes("text-sm text-gray-600")
            audio_upload = ui.upload(
                label="Audio hochladen",
                auto_upload=True,
            ).props('accept=".wav,.mp3,.m4a,.ogg,.webm,.mp4,.mpeg,.mpga"').classes("w-full")

        with ui.card().classes("w-full"):
            ui.label("Aktuelle Frage von Florian").classes("text-sm text-gray-600")
            current_question_label = ui.label(state.current_question).classes(
                "text-xl font-medium whitespace-pre-wrap"
            )

        with ui.card().classes("w-full"):
            ui.label("Zuletzt erkannte Antwort").classes("text-sm text-gray-600")
            recognized_answer_label = ui.label(state.recognized_answer).classes(
                "text-lg whitespace-pre-wrap"
            )

        audio_player = ui.audio(
            state.tts_audio_url,
            controls=False,
            autoplay=True,
        ).style("display: none;")

        ui.separator()

        ui.label("Verlauf").classes("text-lg font-semibold")
        chat_container = ui.column().classes("w-full gap-2")

        ui.separator()

        ui.label("Zusammenfassung").classes("text-lg font-semibold")
        summary_label = ui.label("").classes("whitespace-pre-wrap w-full")

        ui.label("Bericht").classes("text-lg font-semibold")
        report_label = ui.label("").classes("whitespace-pre-wrap w-full")

    footer = ui.footer().classes("w-full bg-gray-100 border-t")
    with footer:
        status_label = ui.label(f"Status: {state.status}").classes(
            "w-full max-w-5xl mx-auto p-3"
        )

    def refresh_view() -> None:
        current_question_label.set_text(state.current_question)
        recognized_answer_label.set_text(state.recognized_answer)
        status_label.set_text(f"Status: {state.status}")
        summary_label.set_text(state.summary)
        report_label.set_text(state.report)

        if state.tts_audio_url:
            audio_player.set_source(state.tts_audio_url)
            audio_player.run_method("load")
            audio_player.run_method("play")
        else:
            audio_player.set_source("")

        chat_container.clear()
        with chat_container:
            for message in state.messages:
                prefix = {
                    "assistant": "Florian",
                    "user": "Erkannt",
                    "system": "System",
                }[message.role]

                color_class = {
                    "assistant": "bg-blue-50",
                    "user": "bg-green-50",
                    "system": "bg-gray-50",
                }[message.role]

                with ui.card().classes(f"w-full {color_class}"):
                    ui.label(prefix).classes("text-sm text-gray-600")
                    ui.label(message.text).classes("whitespace-pre-wrap")

    def on_start() -> None:
        start_ui_session(state)
        refresh_view()

    def on_submit() -> None:
        handle_text_input(state, text_input.value or "")
        text_input.set_value("")
        refresh_view()

    def on_audio_upload(e: events.UploadEventArguments) -> None:
        try:
            state.status = "Speichere Audio"
            refresh_view()

            uploaded_name = e.name or "audio_upload"
            suffix = Path(uploaded_name).suffix.lower() or ".wav"
            target_path = create_uploaded_audio_path(suffix=suffix)

            target_path.write_bytes(e.content.read())

            state.status = "Transkribiere Audio"
            refresh_view()

            transcript = transcribe_audio_file(target_path)
            handle_text_input(state, transcript)

            state.status = "Audio verarbeitet"
        except Exception as exc:
            state.status = f"Fehler bei Audioverarbeitung: {exc}"
            append_message(state, "system", f"Fehler bei Audioverarbeitung: {exc}")
        refresh_view()

    start_button.on_click(on_start)
    text_input.on("keydown.enter", lambda _: on_submit())
    audio_upload.on_upload(on_audio_upload)

    refresh_view()


def run_app() -> None:
    build_ui()
    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    run_app()