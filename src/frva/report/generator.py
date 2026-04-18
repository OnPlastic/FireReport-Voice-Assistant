"""Einfache Textgenerierung für den FRVA-MVP-Bericht."""

from frva.model.report_schema import ReportState


def _join_list(values: list[str]) -> str:
    """Verbindet Listeneinträge zu einem lesbaren Text."""
    if not values:
        return ""

    if len(values) == 1:
        return values[0]

    if len(values) == 2:
        return f"{values[0]} und {values[1]}"

    return ", ".join(values[:-1]) + f" und {values[-1]}"


def generate_report_text(state: ReportState) -> str:
    """Erzeugt einen einfachen Fließtext aus dem aktuellen Berichtszustand."""
    einsatzart = state.einsatzart.value or "ein Einsatz"
    ort = state.ort.value or "unbekanntem Ort"
    datum = state.einsatzdatum.value or "unbekanntem Datum"
    uhrzeit = state.einsatzuhrzeit.value or "unbekannter Uhrzeit"
    fahrzeuge = state.fahrzeuge.value or []
    teilnehmende = state.teilnehmende_feuerwehrleute.value or []
    bemerkungen = state.bemerkungen.value or ""

    report_parts: list[str] = []

    report_parts.append(
        f"Am {datum} um {uhrzeit} fand in {ort} {einsatzart} statt."
    )

    if fahrzeuge:
        fahrzeuge_text = _join_list(fahrzeuge)
        report_parts.append(f"Im Einsatz waren {fahrzeuge_text}.")

    if teilnehmende:
        teilnehmende_text = _join_list(teilnehmende)
        report_parts.append(f"Teilgenommen haben {teilnehmende_text}.")

    if bemerkungen.strip():
        report_parts.append(f"Besondere Bemerkungen: {bemerkungen}")

    return " ".join(report_parts)