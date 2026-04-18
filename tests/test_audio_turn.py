from pathlib import Path

from frva.dialog.audio_turn import process_audio_turn
from frva.dialog.manager import start_dialog
from frva.dialog.state import DialogSession
from frva.model.report_schema import FieldStatus, FieldUpdate


def test_process_audio_turn_uses_transcript_and_extractor(
    monkeypatch,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"fake audio")

    def fake_transcribe_audio_file(
        audio_path: str | Path,
        model_name: str = "base",
        language: str = "de",
    ) -> str:
        assert str(audio_path) == str(audio_file)
        assert model_name == "base"
        assert language == "de"
        return "Es war ein Brand."

    monkeypatch.setattr(
        "frva.dialog.audio_turn.transcribe_audio_file",
        fake_transcribe_audio_file,
    )

    session = DialogSession()
    start_dialog(session)

    transcript, next_question = process_audio_turn(
        session=session,
        audio_path=audio_file,
    )

    assert transcript == "Es war ein Brand."
    assert len(session.report_state.history) == 1
    assert session.report_state.history[0].user_transcript == "Es war ein Brand."
    assert "einsatzart" in session.report_state.field_map()
    assert next_question == "Wo war der Einsatz?"


def test_process_audio_turn_uses_explicit_updates_instead_of_extractor(
    monkeypatch,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"fake audio")

    def fake_transcribe_audio_file(
        audio_path: str | Path,
        model_name: str = "base",
        language: str = "de",
    ) -> str:
        return "Beliebiger Text."

    monkeypatch.setattr(
        "frva.dialog.audio_turn.transcribe_audio_file",
        fake_transcribe_audio_file,
    )

    session = DialogSession()
    start_dialog(session)

    transcript, next_question = process_audio_turn(
        session=session,
        audio_path=audio_file,
        updates={
            "einsatzart": FieldUpdate(
                value="ein Brandeinsatz",
                status=FieldStatus.BESTAETIGT,
            )
        },
    )

    assert transcript == "Beliebiger Text."
    assert session.report_state.einsatzart.value == "ein Brandeinsatz"
    assert session.report_state.einsatzart.status == FieldStatus.BESTAETIGT
    assert next_question == "Wo war der Einsatz?"


def test_process_audio_turn_can_run_without_extractor_and_without_updates(
    monkeypatch,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"fake audio")

    def fake_transcribe_audio_file(
        audio_path: str | Path,
        model_name: str = "base",
        language: str = "de",
    ) -> str:
        return "Freier Text ohne Extraktion."

    monkeypatch.setattr(
        "frva.dialog.audio_turn.transcribe_audio_file",
        fake_transcribe_audio_file,
    )

    session = DialogSession()
    start_dialog(session)

    transcript, next_question = process_audio_turn(
        session=session,
        audio_path=audio_file,
        use_extractor=False,
    )

    assert transcript == "Freier Text ohne Extraktion."
    assert len(session.report_state.history) == 1
    assert session.report_state.einsatzart.value is None
    assert next_question == "Was für ein Einsatz war das?"