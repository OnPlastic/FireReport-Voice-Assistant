from frva.dialog.questions import (
    get_all_fields,
    get_follow_up_question,
    get_question_for_field,
)


def test_get_question_for_field_returns_correct_text() -> None:
    question = get_question_for_field("einsatzart")

    assert question == "Was für ein Einsatz war das?"


def test_get_question_for_field_returns_none_for_unknown_field() -> None:
    question = get_question_for_field("unbekannt")

    assert question is None


def test_get_follow_up_question_returns_uhrzeit_question() -> None:
    question = get_follow_up_question("einsatzuhrzeit")

    assert question == "Zu welcher Uhrzeit ungefähr war der Einsatz?"


def test_get_follow_up_question_returns_datum_question() -> None:
    question = get_follow_up_question("einsatzdatum")

    assert question == "An welchem Datum war der Einsatz?"


def test_get_follow_up_question_returns_none_for_unknown_field() -> None:
    question = get_follow_up_question("unbekannt")

    assert question is None


def test_get_all_fields_contains_expected_fields() -> None:
    fields = get_all_fields()

    expected = {
        "einsatzart",
        "ort",
        "einsatzdatum",
        "fahrzeuge",
        "teilnehmende_feuerwehrleute",
        "bemerkungen",
    }

    assert set(fields) == expected