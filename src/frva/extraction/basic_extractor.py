"""Einfache heuristische Extraktion für den FRVA-MVP."""

from __future__ import annotations

import re

from frva.model.report_schema import FieldStatus, FieldUpdate


def _extract_einsatzart(text: str) -> FieldUpdate[object] | None:
    """Erkennt einfache Einsatzarten anhand von Schlüsselwörtern."""
    lowered = text.lower()

    if "brand" in lowered:
        return FieldUpdate(
            value="ein Brandeinsatz",
            status=FieldStatus.KANDIDAT,
            source_text=text,
            needs_confirmation=True,
        )

    return None


def _extract_ort(text: str) -> FieldUpdate[object] | None:
    """Erkennt einfache Ortsangaben nach 'in <Ort>'."""
    match = re.search(
        r"\bin\s+([A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ-]+)\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    ort = match.group(1)

    return FieldUpdate(
        value=ort,
        status=FieldStatus.KANDIDAT,
        source_text=text,
    )

def test_extract_updates_detects_ort_with_capitalized_in() -> None:
    updates = extract_updates("In Pegnitz.")

    assert "ort" in updates
    assert updates["ort"].value == "Pegnitz"

def _extract_date(text: str) -> FieldUpdate[object] | None:
    """Erkennt ein Datum im Format DD.MM.YYYY."""
    match = re.search(r"\b(\d{2})\.(\d{2})\.(\d{4})\b", text)
    if not match:
        return None

    day, month, year = match.groups()
    iso_date = f"{year}-{month}-{day}"

    return FieldUpdate(
        value=iso_date,
        status=FieldStatus.KANDIDAT,
        source_text=text,
    )


def _extract_time(text: str) -> FieldUpdate[object] | None:
    """Erkennt eine Uhrzeit im Format HH:MM."""
    match = re.search(r"\b(\d{1,2}:\d{2})\b", text)
    if not match:
        return None

    return FieldUpdate(
        value=match.group(1),
        status=FieldStatus.KANDIDAT,
        source_text=text,
    )


def _extract_vehicles(text: str) -> FieldUpdate[object] | None:
    """Erkennt einige einfache Fahrzeugkürzel im Freitext."""
    lowered = text.lower()
    found: list[str] = []

    # Reihenfolge ist wichtig: spezifisch vor allgemein
    vehicle_patterns = [
        (r"\blf\s*10\b", "LF 10"),
        (r"\bmzf\b", "MZF"),
        (r"\bdlk\b", "DLK"),
        (r"\bhlf\b", "HLF"),
        (r"\blf\b", "LF"),
    ]

    for pattern, normalized in vehicle_patterns:
        if re.search(pattern, lowered) and normalized not in found:
            found.append(normalized)

    # Wenn LF 10 erkannt wurde, soll das allgemeinere LF nicht zusätzlich erscheinen
    if "LF 10" in found and "LF" in found:
        found.remove("LF")

    if not found:
        return None

    return FieldUpdate(
        value=found,
        status=FieldStatus.KANDIDAT,
        source_text=text,
        needs_confirmation=True,
    )


def _extract_teilnehmende(text: str) -> FieldUpdate[object] | None:
    """Erkennt sehr einfache Namenslisten über 'und' getrennt.

    Diese Heuristik ist bewusst simpel und nur für Demo-Zwecke gedacht.
    """
    if " und " not in text:
        return None

    parts = [part.strip(" .") for part in text.split(" und ")]
    if len(parts) < 2:
        return None

    # Sehr einfache Heuristik: mindestens zwei Teile, jeweils mit Leerzeichen im Namen
    if not all(" " in part for part in parts):
        return None

    return FieldUpdate(
        value=parts,
        status=FieldStatus.KANDIDAT,
        source_text=text,
        needs_confirmation=True,
    )


def _extract_bemerkungen(text: str) -> FieldUpdate[object] | None:
    """Erkennt einfache Bemerkungen."""
    lowered = text.lower().strip(" .")

    if lowered in {"keine besonderheiten", "nichts besonderes"}:
        return FieldUpdate(
            value="Keine Besonderheiten",
            status=FieldStatus.KANDIDAT,
            source_text=text,
        )

    return None


def extract_updates(text: str) -> dict[str, FieldUpdate[object]]:
    """Extrahiert einfache Feld-Updates aus einem Freitext."""
    updates: dict[str, FieldUpdate[object]] = {}

    einsatzart = _extract_einsatzart(text)
    if einsatzart is not None:
        updates["einsatzart"] = einsatzart

    ort = _extract_ort(text)
    if ort is not None:
        updates["ort"] = ort

    einsatzdatum = _extract_date(text)
    if einsatzdatum is not None:
        updates["einsatzdatum"] = einsatzdatum

    einsatzuhrzeit = _extract_time(text)
    if einsatzuhrzeit is not None:
        updates["einsatzuhrzeit"] = einsatzuhrzeit

    fahrzeuge = _extract_vehicles(text)
    if fahrzeuge is not None:
        updates["fahrzeuge"] = fahrzeuge

    teilnehmende = _extract_teilnehmende(text)
    if teilnehmende is not None:
        updates["teilnehmende_feuerwehrleute"] = teilnehmende

    bemerkungen = _extract_bemerkungen(text)
    if bemerkungen is not None:
        updates["bemerkungen"] = bemerkungen

    return updates