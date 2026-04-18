from frva.ui.app import (
    AppState,
    handle_text_input,
    set_assistant_question,
    start_ui_session,
)


def test_start_ui_session_creates_session_and_first_question() -> None:
    state = AppState()

    first_question = start_ui_session(state)

    assert state.session is not None
    assert state.status == "Warte auf Antwort"
    assert first_question == "Was für ein Einsatz war das?"
    assert len(state.messages) == 1
    assert state.messages[0].role == "assistant"


def test_handle_text_input_auto_starts_session_if_needed() -> None:
    state = AppState()

    next_question = handle_text_input(state, "Es war ein Brand.")

    assert state.session is not None
    assert len(state.messages) >= 2
    assert state.messages[0].role == "assistant"
    assert state.messages[1].role == "user"
    assert next_question == "Wo war der Einsatz?"


def test_handle_text_input_ignores_empty_text() -> None:
    state = AppState()

    result = handle_text_input(state, "   ")

    assert result is None
    assert state.session is None
    assert state.messages == []


def test_handle_text_input_completes_report_when_all_information_arrives() -> None:
    state = AppState()
    start_ui_session(state)

    handle_text_input(state, "Es war ein Brand.")
    handle_text_input(state, "In Pegnitz.")
    handle_text_input(state, "Am 18.04.2026 gegen 19:30 Uhr.")
    handle_text_input(state, "Mit LF 10 und MZF.")
    handle_text_input(state, "Max Mustermann und Erika Musterfrau.")
    final_result = handle_text_input(state, "Keine Besonderheiten.")

    assert final_result is None
    assert state.status == "Bericht vollständig"
    assert "Einsatzübersicht" in state.summary
    assert "Pegnitz" in state.report
    assert any(m.role == "system" for m in state.messages)


def test_set_assistant_question_updates_question_message_and_tts_url() -> None:
    state = AppState()

    def fake_speaker(text: str) -> str | None:
        assert text == "Testfrage"
        return "/tts_audio/test.wav"

    set_assistant_question(state, "Testfrage", speaker=fake_speaker)

    assert state.current_question == "Testfrage"
    assert state.tts_audio_url == "/tts_audio/test.wav"
    assert len(state.messages) == 1
    assert state.messages[0].role == "assistant"


def test_set_assistant_question_handles_missing_tts_gracefully() -> None:
    state = AppState()

    def fake_speaker(text: str) -> str | None:
        return None

    set_assistant_question(state, "Testfrage", speaker=fake_speaker)

    assert state.current_question == "Testfrage"
    assert state.tts_audio_url == ""
    assert len(state.messages) == 1