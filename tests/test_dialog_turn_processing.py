from frva.dialog.manager import process_turn, start_dialog
from frva.dialog.state import DialogSession
from frva.model.report_schema import FieldStatus, FieldUpdate


def test_process_turn_adds_history_entry() -> None:
    session = DialogSession()
    start_dialog(session)

    next_question = process_turn(
        session=session,
        user_transcript="Es war ein Brand.",
        updates={
            "einsatzart": FieldUpdate(
                value="Brand",
                status=FieldStatus.BESTAETIGT,
                source_text="Es war ein Brand.",
            )
        },
    )

    assert len(session.report_state.history) == 1
    assert session.report_state.history[0].assistant_question == "Was für ein Einsatz war das?"
    assert session.report_state.history[0].user_transcript == "Es war ein Brand."
    assert next_question == "Wo war der Einsatz?"


def test_process_turn_applies_updates_to_report_state() -> None:
    session = DialogSession()
    start_dialog(session)

    process_turn(
        session=session,
        user_transcript="Es war ein Brand.",
        updates={
            "einsatzart": FieldUpdate(
                value="Brand",
                status=FieldStatus.BESTAETIGT,
            )
        },
    )

    assert session.report_state.einsatzart.value == "Brand"
    assert session.report_state.einsatzart.status == FieldStatus.BESTAETIGT


def test_process_turn_returns_none_when_dialog_becomes_complete() -> None:
    session = DialogSession()
    start_dialog(session)

    result = process_turn(
        session=session,
        user_transcript="Alles komplett.",
        updates={
            "einsatzart": FieldUpdate(value="Brand", status=FieldStatus.BESTAETIGT),
            "ort": FieldUpdate(value="Pegnitz", status=FieldStatus.BESTAETIGT),
            "einsatzdatum": FieldUpdate(value="2026-04-18", status=FieldStatus.BESTAETIGT),
            "einsatzuhrzeit": FieldUpdate(value="19:30", status=FieldStatus.BESTAETIGT),
            "fahrzeuge": FieldUpdate(value=["LF 10"], status=FieldStatus.BESTAETIGT),
            "teilnehmende_feuerwehrleute": FieldUpdate(
                value=["Max Mustermann"],
                status=FieldStatus.BESTAETIGT,
            ),
            "bemerkungen": FieldUpdate(
                value="Keine Besonderheiten",
                status=FieldStatus.BESTAETIGT,
            ),
        },
    )

    assert result is None
    assert session.finished is True


def test_process_turn_updates_last_question_to_next_open_question() -> None:
    session = DialogSession()
    start_dialog(session)

    next_question = process_turn(
        session=session,
        user_transcript="Es war ein Brand.",
        updates={
            "einsatzart": FieldUpdate(
                value="Brand",
                status=FieldStatus.BESTAETIGT,
            )
        },
    )

    assert next_question == "Wo war der Einsatz?"
    assert session.last_question == "Wo war der Einsatz?"