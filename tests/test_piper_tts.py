"""Piper-TTS-Wrapper für den FRVA-MVP."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PIPER_BINARY = "piper"
DEFAULT_PIPER_MODEL_PATH = Path("models/piper/de_DE-thorsten-high.onnx")
DEFAULT_PIPER_CONFIG_PATH = Path("models/piper/de_DE-thorsten-high.onnx.json")


@dataclass(frozen=True)
class PiperConfig:
    """Konfiguration für die lokale Piper-TTS-Ausgabe."""

    binary: str = DEFAULT_PIPER_BINARY
    model_path: Path = DEFAULT_PIPER_MODEL_PATH
    config_path: Path | None = DEFAULT_PIPER_CONFIG_PATH


def is_piper_available(binary: str = DEFAULT_PIPER_BINARY) -> bool:
    """Prüft, ob das Piper-Binary im System verfügbar ist."""
    return shutil.which(binary) is not None


def synthesize_speech_to_file(
    text: str,
    output_path: str | Path,
    config: PiperConfig | None = None,
) -> Path:
    """Erzeugt aus Text eine WAV-Datei mit Piper.

    Args:
        text:
            Zu sprechender Text.
        output_path:
            Zielpfad der erzeugten WAV-Datei.
        config:
            Optionale Piper-Konfiguration.

    Returns:
        Der Zielpfad als Path.

    Raises:
        ValueError:
            Wenn kein sinnvoller Text übergeben wurde.
        FileNotFoundError:
            Wenn Binary oder Modell fehlen oder keine Datei erzeugt wurde.
        subprocess.CalledProcessError:
            Wenn Piper mit Fehler endet.
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        raise ValueError("Es wurde kein Text zur Sprachausgabe übergeben.")

    cfg = config or PiperConfig()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    if not is_piper_available(cfg.binary):
        raise FileNotFoundError(f"Piper-Binary nicht gefunden: {cfg.binary}")

    if not cfg.model_path.exists():
        raise FileNotFoundError(f"Piper-Modell nicht gefunden: {cfg.model_path}")

    command = [
        cfg.binary,
        "--model",
        str(cfg.model_path),
        "--output_file",
        str(output),
    ]

    if cfg.config_path is not None and cfg.config_path.exists():
        command.extend(["--config", str(cfg.config_path)])

    subprocess.run(
        command,
        input=cleaned_text,
        text=True,
        check=True,
        capture_output=True,
    )

    if not output.exists():
        raise FileNotFoundError(
            f"Piper hat keine Ausgabedatei erzeugt: {output}"
        )

    return output