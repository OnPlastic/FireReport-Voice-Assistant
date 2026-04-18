from frva.dialog.manager import advance_dialog, complete_dialog_if_ready, start_dialog
from frva.dialog.state import DialogSession
from frva.model.report_schema import FieldStatus


def test_start_dialog_marks_session_started() -> None:
    session = DialogSession()

    first_question = start_dialog(session)

    assert session.started is True
    assert first_question == "Was für ein Einsatz war das?"
    assert session.last_question == "Was für ein Einsatz war das?"


def test_advance_dialog_returns_next_question_after_field_is_filled() -> None:
    session = DialogSession()
    start_dialog(session)

    session.report_state.einsatzart.value = "Brand"
    session.report_state.einsatzart.status = FieldStatus.BESTAETIGT

    next_question = advance_dialog(session)

    assert next_question == "Wo war der Einsatz?"
    assert session.last_question == "Wo war der Einsatz?"


def test_advance_dialog_finishes_session_when_no_questions_remain() -> None:
    session = DialogSession()
    start_dialog(session)

    state = session.report_state

    state.einsatzart.value = "Brand"
    state.einsatzart.status = FieldStatus.BESTAETIGT

    state.ort.value = "Pegnitz"
    state.ort.status = FieldStatus.BESTAETIGT

    state.einsatzdatum.value = "2026-04-18"
    state.einsatzdatum.status = FieldStatus.BESTAETIGT

    state.einsatzuhrzeit.value = "19:30"
    state.einsatzuhrzeit.status = FieldStatus.BESTAETIGT

    state.fahrzeuge.value = ["LF 10"]
    state.fahrzeuge.status = FieldStatus.BESTAETIGT

    state.teilnehmende_feuerwehrleute.value = ["Max Mustermann"]
    state.teilnehmende_feuerwehrleute.status = FieldStatus.BESTAETIGT

    state.bemerkungen.value = "Keine Besonderheiten"
    state.bemerkungen.status = FieldStatus.BESTAETIGT

    next_question = advance_dialog(session)

    assert next_question is None
    assert session.finished is True
    assert session.last_question is None


def test_complete_dialog_if_ready_returns_false_when_fields_are_still_open() -> None:
    session = DialogSession()

    result = complete_dialog_if_ready(session)

    assert result is False
    assert session.finished is False


def test_complete_dialog_if_ready_finishes_complete_session() -> None:
    session = DialogSession()
    state = session.report_state

    state.einsatzart.value = "Brand"
    state.einsatzart.status = FieldStatus.BESTAETIGT

    state.ort.value = "Pegnitz"
    state.ort.status = FieldStatus.BESTAETIGT

    state.einsatzdatum.value = "2026-04-18"
    state.einsatzdatum.status = FieldStatus.BESTAETIGT

    state.einsatzuhrzeit.value = "19:30"
    state.einsatzuhrzeit.status = FieldStatus.BESTAETIGT

    state.fahrzeuge.value = ["LF 10"]
    state.fahrzeuge.status = FieldStatus.BESTAETIGT

    state.teilnehmende_feuerwehrleute.value = ["Max Mustermann"]
    state.teilnehmende_feuerwehrleute.status = FieldStatus.BESTAETIGT

    state.bemerkungen.value = "Keine Besonderheiten"
    state.bemerkungen.status = FieldStatus.BESTAETIGT

    result = complete_dialog_if_ready(session)

    assert result is True
    assert session.finished is True
    assert session.last_question is None