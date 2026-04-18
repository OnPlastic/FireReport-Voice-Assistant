"""Fragenkatalog für den FRVA-MVP-Dialog."""

from dataclasses import dataclass
from typing import List


@dataclass
class Question:
    """Repräsentiert eine einzelne Frage im Dialog."""

    field_name: str
    text: str


# Hauptfragen des MVP
QUESTIONS: List[Question] = [
    Question(
        field_name="einsatzart",
        text="Was für ein Einsatz war das?",
    ),
    Question(
        field_name="ort",
        text="Wo war der Einsatz?",
    ),
    Question(
        field_name="einsatzdatum",
        text="Wann war der Einsatz?",
    ),
    Question(
        field_name="fahrzeuge",
        text="Welche Fahrzeuge waren im Einsatz?",
    ),
    Question(
        field_name="teilnehmende_feuerwehrleute",
        text="Wer war alles dabei?",
    ),
    Question(
        field_name="bemerkungen",
        text="Gibt es noch besondere Bemerkungen?",
    ),
]


FOLLOW_UP_QUESTIONS: dict[str, str] = {
    "einsatzdatum": "An welchem Datum war der Einsatz?",
    "einsatzuhrzeit": "Zu welcher Uhrzeit ungefähr war der Einsatz?",
}


def get_question_for_field(field_name: str) -> str | None:
    """Gibt die Hauptfrage für ein bestimmtes Feld zurück."""
    for q in QUESTIONS:
        if q.field_name == field_name:
            return q.text
    return None


def get_follow_up_question(field_name: str) -> str | None:
    """Gibt eine gezielte Nachfrag e für ein Teilfeld zurück."""
    return FOLLOW_UP_QUESTIONS.get(field_name)


def get_all_fields() -> list[str]:
    """Gibt alle bekannten Hauptfeldnamen zurück."""
    return [q.field_name for q in QUESTIONS]