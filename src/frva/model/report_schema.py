"""Datenmodell für den MVP-Berichtszustand des FireReport Voice Assistant.

Diese Datei enthält nur die Kernstrukturen für den internen Berichtszustand.
Noch keine Dialoglogik, keine KI-Anbindung, keine UI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar


T = TypeVar("T")


class FieldStatus(str, Enum):
    """Status eines einzelnen Berichtsfeldes."""

    LEER = "leer"
    KANDIDAT = "kandidat"
    BESTAETIGT = "bestaetigt"


@dataclass
class FieldState(Generic[T]):
    """Zustand eines einzelnen Berichtsfeldes.

    Attributes:
        value:
            Aktueller Feldwert.
        status:
            Bearbeitungsstatus des Feldes.
        confidence:
            Optionale Sicherheit der Extraktion, z. B. 0.0 bis 1.0.
        source_text:
            Transkript-Ausschnitt, aus dem der Feldwert stammt.
        needs_confirmation:
            Kennzeichnet, ob das Feld aktiv bestätigt werden sollte.
    """

    value: T | None = None
    status: FieldStatus = FieldStatus.LEER
    confidence: float | None = None
    source_text: str | None = None
    needs_confirmation: bool = False


@dataclass
class DialogTurn:
    """Ein einzelner Dialogschritt im Verlauf."""

    assistant_question: str
    user_transcript: str
    extracted_updates: dict[str, object] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FieldUpdate(Generic[T]):
    """Beschreibt ein Update für ein einzelnes Berichtsfeld."""

    value: T
    status: FieldStatus = FieldStatus.KANDIDAT
    confidence: float | None = None
    source_text: str | None = None
    needs_confirmation: bool = False


@dataclass
class ReportState:
    """Gesamter interner Zustand des FRVA-MVP-Berichts.

    Hinweis:
    - Datum und Uhrzeit sind intern getrennt modelliert.
    - Im Dialog können sie trotzdem gemeinsam erfragt werden.
    """

    einsatzart: FieldState[str] = field(default_factory=FieldState)
    ort: FieldState[str] = field(default_factory=FieldState)

    einsatzdatum: FieldState[str] = field(default_factory=FieldState)
    einsatzuhrzeit: FieldState[str] = field(default_factory=FieldState)

    fahrzeuge: FieldState[list[str]] = field(
        default_factory=lambda: FieldState(value=[])
    )
    teilnehmende_feuerwehrleute: FieldState[list[str]] = field(
        default_factory=lambda: FieldState(value=[])
    )
    bemerkungen: FieldState[str] = field(default_factory=FieldState)

    current_question: str | None = None
    open_fields: list[str] = field(default_factory=list)
    uncertain_fields: list[str] = field(default_factory=list)
    history: list[DialogTurn] = field(default_factory=list)

    is_complete: bool = False
    is_confirmed: bool = False

    def to_dict(self) -> dict[str, object]:
        """Gibt den kompletten Berichtszustand als Dictionary zurück."""
        return asdict(self)

    def field_map(self) -> dict[str, FieldState[object]]:
        """Gibt alle inhaltlichen Berichtsfelder als Mapping zurück."""
        return {
            "einsatzart": self.einsatzart,
            "ort": self.ort,
            "einsatzdatum": self.einsatzdatum,
            "einsatzuhrzeit": self.einsatzuhrzeit,
            "fahrzeuge": self.fahrzeuge,
            "teilnehmende_feuerwehrleute": self.teilnehmende_feuerwehrleute,
            "bemerkungen": self.bemerkungen,
        }

    def get_open_fields(self) -> list[str]:
        """Ermittelt alle aktuell offenen Berichtsfelder."""
        open_fields: list[str] = []

        for name, field_state in self.field_map().items():
            value = field_state.value

            if value is None:
                open_fields.append(name)
                continue

            if isinstance(value, str) and not value.strip():
                open_fields.append(name)
                continue

            if isinstance(value, list) and len(value) == 0:
                open_fields.append(name)

        return open_fields

    def get_uncertain_fields(self) -> list[str]:
        """Ermittelt alle Felder, die noch unsicher oder unbestätigt sind."""
        uncertain_fields: list[str] = []

        for name, field_state in self.field_map().items():
            if field_state.needs_confirmation:
                uncertain_fields.append(name)
                continue

            if field_state.status == FieldStatus.KANDIDAT:
                uncertain_fields.append(name)

        return uncertain_fields

    def update_completion_status(self) -> None:
        """Setzt is_complete anhand der aktuell offenen Felder."""
        self.is_complete = len(self.get_open_fields()) == 0

    def refresh_meta(self) -> None:
        """Aktualisiert abgeleitete Metadaten des Berichtszustands."""
        self.open_fields = self.get_open_fields()
        self.uncertain_fields = self.get_uncertain_fields()
        self.update_completion_status()

    def apply_field_update(self, field_name: str, update: FieldUpdate[object]) -> None:
        """Wendet ein Update auf genau ein Berichtsfeld an."""
        field_map = self.field_map()

        if field_name not in field_map:
            raise ValueError(f"Unbekanntes Berichtsfeld: {field_name}")

        target_field = field_map[field_name]
        target_field.value = update.value
        target_field.status = update.status
        target_field.confidence = update.confidence
        target_field.source_text = update.source_text
        target_field.needs_confirmation = update.needs_confirmation

        self.refresh_meta()

    def apply_updates(self, updates: dict[str, FieldUpdate[object]]) -> None:
        """Wendet mehrere Feld-Updates nacheinander an."""
        for field_name, update in updates.items():
            self.apply_field_update(field_name, update)
            
    def add_history_turn(
    self,
    assistant_question: str,
    user_transcript: str,
    extracted_updates: dict[str, object] | None = None,
    ) -> None:
        """Fügt einen Dialogschritt zur Verlaufshistorie hinzu."""
        turn = DialogTurn(
            assistant_question=assistant_question,
            user_transcript=user_transcript,
            extracted_updates=extracted_updates or {},
        )
        self.history.append(turn)

    def mark_all_fields_confirmed(self) -> None:
        """Markiert alle aktuell befüllten Berichtsfelder als bestätigt."""
        for field_state in self.field_map().values():
            value = field_state.value

            if value is None:
                continue

            if isinstance(value, str) and not value.strip():
                continue

            if isinstance(value, list) and len(value) == 0:
                continue

            field_state.status = FieldStatus.BESTAETIGT
            field_state.needs_confirmation = False

        self.is_confirmed = True
        self.refresh_meta()

    def reset_confirmation_flags(self) -> None:
        """Entfernt offene Bestätigungsanforderungen aus allen Berichtsfeldern."""
        for field_state in self.field_map().values():
            field_state.needs_confirmation = False

        self.refresh_meta()