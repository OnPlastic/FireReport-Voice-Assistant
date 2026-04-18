from pathlib import Path

import pytest

from frva.asr.whisper_asr import transcribe_audio_file


def test_transcribe_audio_file_raises_for_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        transcribe_audio_file("does_not_exist.wav")


def test_transcribe_audio_file_returns_cleaned_text(monkeypatch, tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"fake audio content")

    class FakeModel:
        def transcribe(self, audio_path: str, language: str = "de") -> dict[str, str]:
            assert audio_path == str(audio_file)
            assert language == "de"
            return {"text": "  Hallo aus Whisper.  "}

    def fake_load_whisper_model(model_name: str = "base") -> FakeModel:
        assert model_name == "base"
        return FakeModel()

    monkeypatch.setattr(
        "frva.asr.whisper_asr.load_whisper_model",
        fake_load_whisper_model,
    )

    result = transcribe_audio_file(audio_file)

    assert result == "Hallo aus Whisper."


def test_transcribe_audio_file_raises_for_empty_transcript(
    monkeypatch,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "empty.wav"
    audio_file.write_bytes(b"fake audio content")

    class FakeModel:
        def transcribe(self, audio_path: str, language: str = "de") -> dict[str, str]:
            return {"text": "   "}

    def fake_load_whisper_model(model_name: str = "base") -> FakeModel:
        return FakeModel()

    monkeypatch.setattr(
        "frva.asr.whisper_asr.load_whisper_model",
        fake_load_whisper_model,
    )

    with pytest.raises(ValueError):
        transcribe_audio_file(audio_file)