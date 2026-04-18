from frva.dialog.manager import get_next_open_field, get_next_question, has_open_questions
from frva.model.report_schema import FieldStatus, ReportState


def test_get_next_open_field_returns_first_field_in_question_order() -> None:
    state = ReportState()

    next_field = get_next_open_field(state)

    assert next_field == "einsatzart"


def test_get_next_open_field_skips_filled_fields() -> None:
    state = ReportState()
    state.einsatzart.value = "Brand"
    state.einsatzart.status = FieldStatus.BESTAETIGT

    next_field = get_next_open_field(state)

    assert next_field == "ort"


def test_get_next_open_field_returns_einsatzdatum_for_open_time_block() -> None:
    state = ReportState()
    state.einsatzart.value = "Brand"
    state.einsatzart.status = FieldStatus.BESTAETIGT
    state.ort.value = "Pegnitz"
    state.ort.status = FieldStatus.BESTAETIGT

    next_field = get_next_open_field(state)

    assert next_field == "einsatzdatum"


def test_get_next_question_returns_question_text_for_next_open_field() -> None:
    state = ReportState()

    next_question = get_next_question(state)

    assert next_question == "Was für ein Einsatz war das?"


def test_get_next_question_returns_combined_time_question_if_datum_and_uhrzeit_are_open() -> None:
    state = ReportState()
    state.einsatzart.value = "Brand"
    state.einsatzart.status = FieldStatus.BESTAETIGT
    state.ort.value = "Pegnitz"
    state.ort.status = FieldStatus.BESTAETIGT

    next_question = get_next_question(state)

    assert next_question == "Wann war der Einsatz?"


def test_get_next_question_returns_uhrzeit_follow_up_if_only_uhrzeit_is_open() -> None:
    state = ReportState()
    state.einsatzart.value = "Brand"
    state.einsatzart.status = FieldStatus.BESTAETIGT
    state.ort.value = "Pegnitz"
    state.ort.status = FieldStatus.BESTAETIGT
    state.einsatzdatum.value = "2026-04-18"
    state.einsatzdatum.status = FieldStatus.BESTAETIGT

    next_question = get_next_question(state)

    assert next_question == "Zu welcher Uhrzeit ungefähr war der Einsatz?"


def test_get_next_question_returns_datum_follow_up_if_only_datum_is_open() -> None:
    state = ReportState()
    state.einsatzart.value = "Brand"
    state.einsatzart.status = FieldStatus.BESTAETIGT
    state.ort.value = "Pegnitz"
    state.ort.status = FieldStatus.BESTAETIGT
    state.einsatzuhrzeit.value = "19:30"
    state.einsatzuhrzeit.status = FieldStatus.BESTAETIGT

    next_question = get_next_question(state)

    assert next_question == "An welchem Datum war der Einsatz?"


def test_get_next_question_returns_none_if_all_fields_are_filled() -> None:
    state = ReportState()

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

    next_question = get_next_question(state)

    assert next_question is None


def test_has_open_questions_returns_true_for_empty_state() -> None:
    state = ReportState()

    assert has_open_questions(state) is True


def test_has_open_questions_returns_false_for_complete_state() -> None:
    state = ReportState()

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

    assert has_open_questions(state) is False