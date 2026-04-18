"""Tests für das MVP-Datenmodell des FRVA."""

from frva.model.report_schema import FieldStatus, FieldUpdate, ReportState


def test_report_state_can_be_created() -> None:
    """Ein leerer ReportState soll ohne Fehler erzeugt werden können."""
    state = ReportState()

    assert state is not None


def test_report_state_has_expected_default_status_values() -> None:
    """Alle einfachen Felder sollen initial leer sein."""
    state = ReportState()

    assert state.einsatzart.status == FieldStatus.LEER
    assert state.ort.status == FieldStatus.LEER
    assert state.einsatzdatum.status == FieldStatus.LEER
    assert state.einsatzuhrzeit.status == FieldStatus.LEER
    assert state.bemerkungen.status == FieldStatus.LEER


def test_report_state_list_fields_start_as_empty_lists() -> None:
    """Listenfelder sollen mit leeren Listen initialisiert werden."""
    state = ReportState()

    assert state.fahrzeuge.value == []
    assert state.teilnehmende_feuerwehrleute.value == []


def test_report_state_meta_fields_have_clean_defaults() -> None:
    """Metadaten sollen mit sinnvollen Anfangswerten starten."""
    state = ReportState()

    assert state.current_question is None
    assert state.open_fields == []
    assert state.uncertain_fields == []
    assert state.history == []
    assert state.is_complete is False
    assert state.is_confirmed is False


def test_report_state_to_dict_returns_expected_top_level_keys() -> None:
    """Die Dictionary-Ausgabe soll die wichtigsten Top-Level-Felder enthalten."""
    state = ReportState()
    data = state.to_dict()

    expected_keys = {
        "einsatzart",
        "ort",
        "einsatzdatum",
        "einsatzuhrzeit",
        "fahrzeuge",
        "teilnehmende_feuerwehrleute",
        "bemerkungen",
        "current_question",
        "open_fields",
        "uncertain_fields",
        "history",
        "is_complete",
        "is_confirmed",
    }

    assert expected_keys.issubset(data.keys())


def test_get_open_fields_returns_all_empty_mvp_fields() -> None:
    """Ein leerer Berichtszustand soll alle fachlichen Felder als offen melden."""
    state = ReportState()

    open_fields = state.get_open_fields()

    expected = {
        "einsatzart",
        "ort",
        "einsatzdatum",
        "einsatzuhrzeit",
        "fahrzeuge",
        "teilnehmende_feuerwehrleute",
        "bemerkungen",
    }

    assert set(open_fields) == expected


def test_get_open_fields_ignores_filled_fields() -> None:
    """Befüllte Felder sollen nicht mehr als offen gelten."""
    state = ReportState()
    state.einsatzart.value = "Brand"
    state.ort.value = "Pegnitz"
    state.fahrzeuge.value = ["LF 10"]

    open_fields = state.get_open_fields()

    assert "einsatzart" not in open_fields
    assert "ort" not in open_fields
    assert "fahrzeuge" not in open_fields


def test_get_uncertain_fields_detects_candidates_and_confirmation_flags() -> None:
    """Unsichere Felder sollen korrekt erkannt werden."""
    state = ReportState()
    state.einsatzart.status = FieldStatus.KANDIDAT
    state.ort.needs_confirmation = True

    uncertain_fields = state.get_uncertain_fields()

    assert "einsatzart" in uncertain_fields
    assert "ort" in uncertain_fields


def test_refresh_meta_updates_open_uncertain_and_complete_flags() -> None:
    """refresh_meta soll alle abgeleiteten Metadaten korrekt setzen."""
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

    state.refresh_meta()

    assert state.open_fields == []
    assert state.uncertain_fields == []
    assert state.is_complete is True


def test_apply_field_update_updates_single_field() -> None:
    """Ein einzelnes Feld-Update soll korrekt übernommen werden."""
    state = ReportState()

    update = FieldUpdate(
        value="Brand",
        status=FieldStatus.KANDIDAT,
        confidence=0.91,
        source_text="Es war ein Brand im Schuppen",
        needs_confirmation=True,
    )

    state.apply_field_update("einsatzart", update)

    assert state.einsatzart.value == "Brand"
    assert state.einsatzart.status == FieldStatus.KANDIDAT
    assert state.einsatzart.confidence == 0.91
    assert state.einsatzart.source_text == "Es war ein Brand im Schuppen"
    assert state.einsatzart.needs_confirmation is True


def test_apply_field_update_refreshes_meta_data() -> None:
    """Nach einem Feld-Update sollen die Metadaten aktualisiert werden."""
    state = ReportState()

    update = FieldUpdate(
        value="Pegnitz",
        status=FieldStatus.BESTAETIGT,
        confidence=0.99,
        source_text="in Pegnitz",
        needs_confirmation=False,
    )

    state.apply_field_update("ort", update)

    assert "ort" not in state.open_fields
    assert "ort" not in state.uncertain_fields


def test_apply_field_update_raises_for_unknown_field() -> None:
    """Unbekannte Feldnamen sollen einen klaren Fehler auslösen."""
    state = ReportState()

    update = FieldUpdate(value="test")

    try:
        state.apply_field_update("unbekanntes_feld", update)
        assert False, "ValueError wurde erwartet"
    except ValueError as exc:
        assert "Unbekanntes Berichtsfeld" in str(exc)


def test_apply_updates_updates_multiple_fields() -> None:
    """Mehrere Feld-Updates sollen in einem Schritt übernommen werden."""
    state = ReportState()

    updates = {
        "einsatzart": FieldUpdate(
            value="Brand",
            status=FieldStatus.BESTAETIGT,
            source_text="Brand",
        ),
        "ort": FieldUpdate(
            value="Pegnitz",
            status=FieldStatus.BESTAETIGT,
            source_text="in Pegnitz",
        ),
        "fahrzeuge": FieldUpdate(
            value=["LF 10", "MZF"],
            status=FieldStatus.KANDIDAT,
            source_text="mit LF 10 und MZF",
            needs_confirmation=True,
        ),
    }

    state.apply_updates(updates)

    assert state.einsatzart.value == "Brand"
    assert state.ort.value == "Pegnitz"
    assert state.fahrzeuge.value == ["LF 10", "MZF"]

    assert state.einsatzart.status == FieldStatus.BESTAETIGT
    assert state.ort.status == FieldStatus.BESTAETIGT
    assert state.fahrzeuge.status == FieldStatus.KANDIDAT

    assert "fahrzeuge" in state.uncertain_fields
    
    
def test_add_history_turn_appends_dialog_turn() -> None:
    """Ein Dialogschritt soll korrekt in die Historie übernommen werden."""
    state = ReportState()

    state.add_history_turn(
        assistant_question="Wann war der Einsatz?",
        user_transcript="Gestern gegen halb acht.",
        extracted_updates={
            "einsatzdatum": "gestern",
            "einsatzuhrzeit": "19:30",
        },
    )

    assert len(state.history) == 1
    assert state.history[0].assistant_question == "Wann war der Einsatz?"
    assert state.history[0].user_transcript == "Gestern gegen halb acht."
    assert state.history[0].extracted_updates["einsatzdatum"] == "gestern"


def test_mark_all_fields_confirmed_marks_only_filled_fields() -> None:
    """Nur befüllte Felder sollen als bestätigt markiert werden."""
    state = ReportState()

    state.einsatzart.value = "Brand"
    state.einsatzart.status = FieldStatus.KANDIDAT
    state.einsatzart.needs_confirmation = True

    state.ort.value = "Pegnitz"
    state.ort.status = FieldStatus.KANDIDAT
    state.ort.needs_confirmation = True

    state.mark_all_fields_confirmed()

    assert state.einsatzart.status == FieldStatus.BESTAETIGT
    assert state.einsatzart.needs_confirmation is False
    assert state.ort.status == FieldStatus.BESTAETIGT
    assert state.ort.needs_confirmation is False
    assert state.is_confirmed is True


def test_mark_all_fields_confirmed_refreshes_uncertain_fields() -> None:
    """Nach globaler Bestätigung sollen unsichere Felder verschwinden."""
    state = ReportState()

    state.einsatzart.value = "Brand"
    state.einsatzart.status = FieldStatus.KANDIDAT
    state.einsatzart.needs_confirmation = True

    state.refresh_meta()
    assert "einsatzart" in state.uncertain_fields

    state.mark_all_fields_confirmed()

    assert "einsatzart" not in state.uncertain_fields


def test_reset_confirmation_flags_clears_needs_confirmation() -> None:
    """Alle Bestätigungsflags sollen zurückgesetzt werden können."""
    state = ReportState()

    state.einsatzart.needs_confirmation = True
    state.ort.needs_confirmation = True

    state.reset_confirmation_flags()

    assert state.einsatzart.needs_confirmation is False
    assert state.ort.needs_confirmation is False