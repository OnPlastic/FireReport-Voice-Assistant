from frva.extraction.basic_extractor import extract_updates
from frva.model.report_schema import FieldStatus


def test_extract_updates_detects_brand() -> None:
    updates = extract_updates("Es war ein Brand im Gebäude.")

    assert "einsatzart" in updates
    assert updates["einsatzart"].value == "ein Brandeinsatz"
    assert updates["einsatzart"].status == FieldStatus.KANDIDAT
    assert updates["einsatzart"].needs_confirmation is True


def test_extract_updates_detects_date_and_converts_to_iso() -> None:
    updates = extract_updates("Der Einsatz war am 18.04.2026.")

    assert "einsatzdatum" in updates
    assert updates["einsatzdatum"].value == "2026-04-18"


def test_extract_updates_detects_time() -> None:
    updates = extract_updates("Beginn war um 19:30 Uhr.")

    assert "einsatzuhrzeit" in updates
    assert updates["einsatzuhrzeit"].value == "19:30"


def test_extract_updates_detects_multiple_vehicles() -> None:
    updates = extract_updates("Wir waren mit LF 10 und MZF vor Ort.")

    assert "fahrzeuge" in updates
    assert updates["fahrzeuge"].value == ["LF 10", "MZF"]
    assert updates["fahrzeuge"].needs_confirmation is True


def test_extract_updates_returns_empty_dict_for_unmatched_text() -> None:
    updates = extract_updates("Hallo zusammen.")

    assert updates == {}