from frva.model.report_schema import ReportState
from frva.report.generator import generate_report_text


def test_generate_report_text_returns_basic_sentence_for_empty_state() -> None:
    state = ReportState()

    text = generate_report_text(state)

    assert "Am unbekanntem Datum um unbekannter Uhrzeit" in text
    assert "fand in unbekanntem Ort ein Einsatz statt." in text


def test_generate_report_text_includes_main_fields() -> None:
    state = ReportState()
    state.einsatzart.value = "ein Brandeinsatz"
    state.ort.value = "Pegnitz"
    state.einsatzdatum.value = "2026-04-18"
    state.einsatzuhrzeit.value = "19:30"

    text = generate_report_text(state)

    assert text == "Am 2026-04-18 um 19:30 fand in Pegnitz ein Brandeinsatz statt."


def test_generate_report_text_includes_vehicles() -> None:
    state = ReportState()
    state.einsatzart.value = "ein Brandeinsatz"
    state.ort.value = "Pegnitz"
    state.einsatzdatum.value = "2026-04-18"
    state.einsatzuhrzeit.value = "19:30"
    state.fahrzeuge.value = ["LF 10", "MZF"]

    text = generate_report_text(state)

    assert "Im Einsatz waren LF 10 und MZF." in text


def test_generate_report_text_includes_participants() -> None:
    state = ReportState()
    state.einsatzart.value = "ein Brandeinsatz"
    state.ort.value = "Pegnitz"
    state.einsatzdatum.value = "2026-04-18"
    state.einsatzuhrzeit.value = "19:30"
    state.teilnehmende_feuerwehrleute.value = ["Max Mustermann", "Erika Musterfrau"]

    text = generate_report_text(state)

    assert "Teilgenommen haben Max Mustermann und Erika Musterfrau." in text


def test_generate_report_text_includes_remarks() -> None:
    state = ReportState()
    state.einsatzart.value = "ein Brandeinsatz"
    state.ort.value = "Pegnitz"
    state.einsatzdatum.value = "2026-04-18"
    state.einsatzuhrzeit.value = "19:30"
    state.bemerkungen.value = "Keine Besonderheiten"

    text = generate_report_text(state)

    assert "Besondere Bemerkungen: Keine Besonderheiten" in text


def test_generate_report_text_handles_three_list_entries() -> None:
    state = ReportState()
    state.einsatzart.value = "ein Brandeinsatz"
    state.ort.value = "Pegnitz"
    state.einsatzdatum.value = "2026-04-18"
    state.einsatzuhrzeit.value = "19:30"
    state.fahrzeuge.value = ["LF 10", "MZF", "DLK"]

    text = generate_report_text(state)

    assert "Im Einsatz waren LF 10, MZF und DLK." in text