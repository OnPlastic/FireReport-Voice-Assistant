"""Einfache Formatierung des aktuellen Berichtszustands."""

from frva.model.report_schema import ReportState


def _format_list(values: list[str]) -> str:
    """Formatiert eine Liste von Strings lesbar für die Ausgabe."""
    if not values:
        return "-"

    return ", ".join(values)


def format_report_summary(state: ReportState) -> str:
    """Erzeugt eine einfache, strukturierte Zusammenfassung des Berichtszustands."""
    einsatzart = state.einsatzart.value or "-"
    ort = state.ort.value or "-"
    einsatzdatum = state.einsatzdatum.value or "-"
    einsatzuhrzeit = state.einsatzuhrzeit.value or "-"
    fahrzeuge = _format_list(state.fahrzeuge.value or [])
    teilnehmende = _format_list(state.teilnehmende_feuerwehrleute.value or [])
    bemerkungen = state.bemerkungen.value or "-"

    return (
        "Einsatzübersicht\n"
        "-----------------\n"
        f"Einsatzart: {einsatzart}\n"
        f"Ort: {ort}\n"
        f"Datum: {einsatzdatum}\n"
        f"Uhrzeit: {einsatzuhrzeit}\n"
        f"Fahrzeuge: {fahrzeuge}\n"
        f"Teilnehmende Feuerwehrleute: {teilnehmende}\n"
        f"Bemerkungen: {bemerkungen}"
    )