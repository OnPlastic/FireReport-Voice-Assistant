from frva.model.report_schema import ReportState
from frva.report.formatter import format_report_summary


def test_format_report_summary_returns_basic_heading() -> None:
    state = ReportState()

    summary = format_report_summary(state)

    assert "Einsatzübersicht" in summary


def test_format_report_summary_shows_placeholder_for_empty_fields() -> None:
    state = ReportState()

    summary = format_report_summary(state)

    assert "Einsatzart: -" in summary
    assert "Ort: -" in summary
    assert "Datum: -" in summary
    assert "Uhrzeit: -" in summary
    assert "Fahrzeuge: -" in summary
    assert "Teilnehmende Feuerwehrleute: -" in summary
    assert "Bemerkungen: -" in summary


def test_format_report_summary_renders_filled_values() -> None:
    state = ReportState()

    state.einsatzart.value = "Brand"
    state.ort.value = "Pegnitz"
    state.einsatzdatum.value = "2026-04-18"
    state.einsatzuhrzeit.value = "19:30"
    state.fahrzeuge.value = ["LF 10", "MZF"]
    state.teilnehmende_feuerwehrleute.value = ["Max Mustermann", "Erika Musterfrau"]
    state.bemerkungen.value = "Keine Besonderheiten"

    summary = format_report_summary(state)

    assert "Einsatzart: Brand" in summary
    assert "Ort: Pegnitz" in summary
    assert "Datum: 2026-04-18" in summary
    assert "Uhrzeit: 19:30" in summary
    assert "Fahrzeuge: LF 10, MZF" in summary
    assert "Teilnehmende Feuerwehrleute: Max Mustermann, Erika Musterfrau" in summary
    assert "Bemerkungen: Keine Besonderheiten" in summary