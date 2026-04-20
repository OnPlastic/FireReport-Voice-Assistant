"""NiceGUI-Oberfläche für den FRVA-MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from uuid import uuid4

from nicegui import app, ui

from frva.audio.recorder import create_recorded_audio_path, save_data_url_audio
from frva.asr.whisper_asr import transcribe_audio_file
from frva.dialog.manager import process_turn, start_dialog
from frva.dialog.state import DialogSession
from frva.extraction.basic_extractor import extract_updates
from frva.nlp.gemini_extractor import extract_updates_with_gemini
from frva.report.formatter import format_report_summary
from frva.report.generator import generate_report_text
from frva.tts.piper_tts import synthesize_speech_to_file


Role = Literal["assistant", "user", "system"]

TTS_OUTPUT_DIR = Path("data/output/tts")
TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TTS_ROUTE = "/tts_audio"


@dataclass
class ChatMessage:
    role: Role
    text: str


@dataclass
class AppState:
    session: DialogSession | None = None
    status: str = "Bereit"
    messages: list[ChatMessage] = field(default_factory=list)
    tts_audio_url: str = ""
    summary: str = ""
    report: str = ""


def append_message(state: AppState, role: Role, text: str) -> None:
    state.messages.append(ChatMessage(role=role, text=text))


def speak_text_to_url(text: str) -> str:
    output_path = TTS_OUTPUT_DIR / f"tts_{uuid4().hex}.wav"
    synthesize_speech_to_file(text, output_path)
    return f"{TTS_ROUTE}/{output_path.name}"


def set_assistant_question(state: AppState, question: str | None) -> None:
    print("=== SET_ASSISTANT_QUESTION ===")
    print(question)
    print("==============================")

    if question is None:
        return

    append_message(state, "assistant", question)
    state.status = "Florian spricht ..."
    audio_url = speak_text_to_url(question)
    state.tts_audio_url = audio_url or ""


def start_ui_session(state: AppState) -> None:
    state.session = DialogSession()
    state.messages.clear()
    state.tts_audio_url = ""
    state.summary = ""
    state.report = ""
    state.status = "Dialog gestartet"

    first_question = start_dialog(state.session)

    print("=== FIRST QUESTION ===")
    print(first_question)
    print("======================")

    if first_question:
        set_assistant_question(state, first_question)
        state.status = "Warte auf Antwort"
    else:
        state.status = "Bericht vollständig"


def extract_updates_for_text(text: str) -> dict:
    try:
        updates = extract_updates_with_gemini(text)
        if updates:
            return updates
    except Exception as exc:
        print(f"Gemini Fehler: {exc}")

    return extract_updates(text)


def handle_text_input(state: AppState, text: str) -> None:
    cleaned_text = text.strip()
    if not cleaned_text:
        return

    if state.session is None:
        start_ui_session(state)

    append_message(state, "user", cleaned_text)
    state.status = "Analysiere Antwort ..."

    updates = extract_updates_for_text(cleaned_text)
    print("=== APP UPDATES ===")
    print(updates)
    print("===================")

    next_question = process_turn(
        session=state.session,
        user_transcript=cleaned_text,
        updates=updates,
    )

    print("=== NEXT QUESTION ===")
    print(next_question)
    print("=====================")

    if next_question:
        set_assistant_question(state, next_question)
        state.status = "Warte auf Antwort"
    else:
        append_message(state, "system", "Danke, der Bericht ist vollständig.")
        state.status = "Fertig"
        if state.session is not None:
            state.summary = format_report_summary(state.session.report_state)
            state.report = generate_report_text(state.session.report_state)

    print("=== HANDLE_TEXT_INPUT DONE ===")


def build_browser_recorder_js() -> str:
    return r"""
        (async () => {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            return await new Promise(async (resolve, reject) => {
                let mimeType = '';
                if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                    mimeType = 'audio/webm;codecs=opus';
                } else if (MediaRecorder.isTypeSupported('audio/webm')) {
                    mimeType = 'audio/webm';
                } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
                    mimeType = 'audio/ogg;codecs=opus';
                }

                const options = mimeType
                    ? { mimeType, audioBitsPerSecond: 16000 }
                    : { audioBitsPerSecond: 16000 };

                const recorder = new MediaRecorder(stream, options);
                const chunks = [];

                const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                const audioContext = new AudioContextClass();
                const source = audioContext.createMediaStreamSource(stream);
                const analyser = audioContext.createAnalyser();

                analyser.fftSize = 1024;
                source.connect(analyser);

                const data = new Uint8Array(analyser.fftSize);

                const silenceThreshold = 6;
                const silenceDurationMs = 2200;
                const startupGraceMs = 1500;
                const maxRecordingMs = 6000;

                let silenceStart = null;
                let stopped = false;
                let monitoringStarted = false;
                let maxTimeoutId = null;

                const cleanup = async () => {
                    try {
                        stream.getTracks().forEach(track => track.stop());
                    } catch (e) {
                    }

                    try {
                        source.disconnect();
                    } catch (e) {
                    }

                    try {
                        analyser.disconnect();
                    } catch (e) {
                    }

                    try {
                        await audioContext.close();
                    } catch (e) {
                    }

                    if (maxTimeoutId !== null) {
                        clearTimeout(maxTimeoutId);
                    }
                };

                const stopRecorder = () => {
                    if (stopped) {
                        return;
                    }
                    stopped = true;
                    try {
                        recorder.stop();
                    } catch (e) {
                    }
                };

                recorder.ondataavailable = (event) => {
                    if (event.data && event.data.size > 0) {
                        chunks.push(event.data);
                    }
                };

                recorder.onerror = async (event) => {
                    await cleanup();
                    reject(event.error || new Error('Recorder-Fehler'));
                };

                recorder.onstop = async () => {
                    try {
                        const blob = new Blob(
                            chunks,
                            { type: recorder.mimeType || mimeType || 'audio/webm' }
                        );

                        if (blob.size === 0) {
                            await cleanup();
                            reject(new Error('Leere Audioaufnahme.'));
                            return;
                        }

                        const reader = new FileReader();
                        reader.onloadend = async () => {
                            await cleanup();
                            resolve({
                                mimeType: blob.type || recorder.mimeType || mimeType || 'audio/webm',
                                dataUrl: reader.result,
                                size: blob.size,
                            });
                        };
                        reader.onerror = async () => {
                            await cleanup();
                            reject(new Error('Audio konnte nicht gelesen werden.'));
                        };
                        reader.readAsDataURL(blob);
                    } catch (error) {
                        await cleanup();
                        reject(error);
                    }
                };

                const checkSilence = () => {
                    if (stopped) {
                        return;
                    }

                    analyser.getByteTimeDomainData(data);

                    let sumSquares = 0;
                    for (let i = 0; i < data.length; i++) {
                        const normalized = (data[i] - 128) / 128;
                        sumSquares += normalized * normalized;
                    }

                    const rms = Math.sqrt(sumSquares / data.length);
                    const level = rms * 1000;

                    if (!monitoringStarted) {
                        requestAnimationFrame(checkSilence);
                        return;
                    }

                    if (level < silenceThreshold) {
                        if (silenceStart === null) {
                            silenceStart = performance.now();
                        } else if (performance.now() - silenceStart >= silenceDurationMs) {
                            stopRecorder();
                            return;
                        }
                    } else {
                        silenceStart = null;
                    }

                    requestAnimationFrame(checkSilence);
                };

                recorder.start(250);

                setTimeout(() => {
                    monitoringStarted = true;
                }, startupGraceMs);

                maxTimeoutId = setTimeout(() => {
                    stopRecorder();
                }, maxRecordingMs);

                requestAnimationFrame(checkSilence);
            });
        })()
    """


def suffix_from_mime_type(mime_type: str) -> str:
    lowered = mime_type.lower()

    if "ogg" in lowered:
        return ".ogg"
    if "mp4" in lowered or "mpeg" in lowered or "m4a" in lowered:
        return ".m4a"
    return ".webm"


def build_ui() -> None:
    app.add_static_files(TTS_ROUTE, str(TTS_OUTPUT_DIR))

    state = AppState()

    with ui.column().classes("w-full max-w-3xl mx-auto p-4 gap-4 pb-24"):
        ui.label("FireReport Voice Assistant").classes("text-3xl font-bold")

        with ui.row().classes("gap-3"):
            start_button = ui.button("Dialog starten").classes("px-6 py-2")
            record_button = ui.button("Antwort aufnehmen").classes("px-6 py-2")
            text_toggle_button = ui.button("Textantwort").classes("px-6 py-2")

        manual_text_input = ui.input(
            placeholder="Fallback: Antwort hier eintippen und Enter drücken ...",
        ).classes("w-full")
        manual_text_input.set_visibility(False)

        chat_container = ui.column().classes("w-full gap-3")

        audio_player = ui.audio(
            state.tts_audio_url,
            controls=False,
            autoplay=True,
        ).style("display: none;")

    footer = ui.footer().classes("w-full bg-gray-100 border-t")
    with footer:
        status_label = ui.label(state.status).classes(
            "w-full max-w-3xl mx-auto p-3 text-black"
        )

    def refresh_view() -> None:
        status_label.set_text(state.status)

        if state.tts_audio_url:
            audio_player.set_source(state.tts_audio_url)
            audio_player.play()

        chat_container.clear()
        with chat_container:
            for message in state.messages:
                if message.role == "assistant":
                    align = "items-start"
                    color = "bg-blue-50"
                elif message.role == "user":
                    align = "items-end"
                    color = "bg-green-50"
                else:
                    align = "items-center"
                    color = "bg-gray-50"

                with ui.row().classes(f"w-full {align}"):
                    with ui.card().classes(f"{color} max-w-xl"):
                        ui.label(message.text).classes("whitespace-pre-wrap")

    def on_start() -> None:
        try:
            start_ui_session(state)
        except Exception as exc:
            state.status = f"Fehler beim Start: {exc}"
            append_message(state, "system", f"Fehler beim Start: {exc}")
        refresh_view()

    async def on_record() -> None:
        try:
            if state.session is None:
                start_ui_session(state)
                refresh_view()

            state.status = "Höre zu ..."
            refresh_view()

            result = await ui.run_javascript(
                build_browser_recorder_js(),
                timeout=15.0,
            )

            if not result:
                raise RuntimeError("Browser-Aufnahme hat kein Ergebnis geliefert.")

            mime_type = str(result.get("mimeType", "audio/webm"))
            data_url = str(result.get("dataUrl", ""))
            payload_size = int(result.get("size", 0))

            print(f"Audio-Payload-Größe: {payload_size} Bytes")

            if not data_url:
                raise RuntimeError("Browser-Aufnahme enthält keine Audiodaten.")

            suffix = suffix_from_mime_type(mime_type)
            target_path = create_recorded_audio_path(suffix=suffix)
            save_data_url_audio(data_url, target_path)

            state.status = "Transkribiere Audio ..."
            refresh_view()

            transcript = transcribe_audio_file(target_path)
            print("=== TRANSCRIPT ===")
            print(transcript)
            print("==================")

            handle_text_input(state, transcript)

            state.status = "Warte auf Antwort"
        except Exception as exc:
            state.status = f"Fehler bei Audioaufnahme: {exc}"
            append_message(state, "system", f"Fehler bei Audioaufnahme: {exc}")
        refresh_view()

    def on_text_toggle() -> None:
        manual_text_input.set_visibility(not manual_text_input.visible)

    def on_manual_submit() -> None:
        try:
            handle_text_input(state, manual_text_input.value or "")
            manual_text_input.set_value("")
        except Exception as exc:
            state.status = f"Fehler bei Texteingabe: {exc}"
            append_message(state, "system", f"Fehler bei Texteingabe: {exc}")
        refresh_view()

    start_button.on_click(on_start)
    record_button.on_click(on_record)
    text_toggle_button.on_click(on_text_toggle)
    manual_text_input.on("keydown.enter", lambda _: on_manual_submit())

    refresh_view()


def run_app() -> None:
    build_ui()
    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    run_app()