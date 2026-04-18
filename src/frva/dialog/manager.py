"""Einfache regelbasierte Dialogsteuerung für den FRVA-MVP."""

from frva.dialog.questions import (
    QUESTIONS,
    get_follow_up_question,
    get_question_for_field,
)
from frva.dialog.state import DialogSession
from frva.model.report_schema import FieldUpdate, ReportState


def get_next_open_field(state: ReportState) -> str | None:
    """Gibt das nächste offene Hauptfeld in der definierten Fragenreihenfolge zurück.

    Zeitlogik:
    - einsatzdatum ist das Hauptfeld für den gemeinsamen Zeitblock
    - einsatzuhrzeit wird nicht separat in QUESTIONS geführt
    - sobald der Zeitblock in der Reihenfolge erreicht ist, wird geprüft:
      ob datum oder uhrzeit noch offen sind
    """
    state.refresh_meta()

    open_fields = set(state.open_fields)

    for question in QUESTIONS:
        if question.field_name == "einsatzdatum":
            if "einsatzdatum" in open_fields or "einsatzuhrzeit" in open_fields:
                return "einsatzdatum"
            continue

        if question.field_name in open_fields:
            return question.field_name

    return None

def get_next_question(state: ReportState) -> str | None:
    """Gibt die nächste passende Frage für den aktuellen Berichtszustand zurück.

    Regeln:
    - Reihenfolge folgt zuerst den Hauptfeldern aus QUESTIONS
    - Für den Zeitblock gilt:
      * wenn datum und uhrzeit offen sind -> gemeinsame Erstfrage
      * wenn nur uhrzeit offen ist -> Nachfrage nach Uhrzeit
      * wenn nur datum offen ist -> Nachfrage nach Datum
    """
    state.refresh_meta()

    next_field = get_next_open_field(state)

    if next_field is None:
        return None

    # Speziallogik nur dann anwenden, wenn der Zeitblock tatsächlich als nächstes dran ist
    if next_field == "einsatzdatum":
        datum_offen = "einsatzdatum" in state.open_fields
        uhrzeit_offen = "einsatzuhrzeit" in state.open_fields

        if datum_offen and uhrzeit_offen:
            return get_question_for_field("einsatzdatum")

        if not datum_offen and uhrzeit_offen:
            return get_follow_up_question("einsatzuhrzeit")

        if datum_offen and not uhrzeit_offen:
            return get_follow_up_question("einsatzdatum")

    return get_question_for_field(next_field)


def has_open_questions(state: ReportState) -> bool:
    """Prüft, ob noch mindestens ein fachliches Feld offen ist."""
    state.refresh_meta()
    return len(state.open_fields) > 0


def start_dialog(session: DialogSession) -> str | None:
    """Startet eine Dialogsitzung und setzt die erste Frage."""
    session.start()

    first_question = get_next_question(session.report_state)
    session.set_last_question(first_question)

    if first_question is None:
        session.finish()

    return first_question


def advance_dialog(session: DialogSession) -> str | None:
    """Ermittelt die nächste Frage und aktualisiert den Sitzungszustand."""
    next_question = get_next_question(session.report_state)
    session.set_last_question(next_question)

    if next_question is None:
        session.finish()

    return next_question


def complete_dialog_if_ready(session: DialogSession) -> bool:
    """Schließt die Sitzung ab, wenn keine offenen Fragen mehr bestehen."""
    if not has_open_questions(session.report_state):
        session.finish()
        session.set_last_question(None)
        return True

    return False


def process_turn(
    session: DialogSession,
    user_transcript: str,
    updates: dict[str, FieldUpdate[object]],
) -> str | None:
    """Verarbeitet einen einzelnen Dialogschritt auf Basis bereits vorliegender Updates."""
    session.report_state.add_history_turn(
        assistant_question=session.last_question or "",
        user_transcript=user_transcript,
        extracted_updates=updates,
    )

    session.report_state.apply_updates(updates)

    if complete_dialog_if_ready(session):
        return None

    return advance_dialog(session)