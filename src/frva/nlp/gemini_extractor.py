"""Gemini-basierte Extraktion für freie Nutzerantworten im FRVA-MVP."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from frva.model.report_schema import FieldStatus, FieldUpdate


env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
CURRENT_REFERENCE_DATE = "2026-04-18"


EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "einsatzart": {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "confidence": {"type": "number"},
                "needs_confirmation": {"type": "boolean"},
            },
            "required": ["value", "confidence", "needs_confirmation"],
        },
        "ort": {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "confidence": {"type": "number"},
                "needs_confirmation": {"type": "boolean"},
            },
            "required": ["value", "confidence", "needs_confirmation"],
        },
        "einsatzdatum": {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "confidence": {"type": "number"},
                "needs_confirmation": {"type": "boolean"},
            },
            "required": ["value", "confidence", "needs_confirmation"],
        },
        "einsatzuhrzeit": {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "confidence": {"type": "number"},
                "needs_confirmation": {"type": "boolean"},
            },
            "required": ["value", "confidence", "needs_confirmation"],
        },
        "fahrzeuge": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "confidence": {"type": "number"},
                "needs_confirmation": {"type": "boolean"},
            },
            "required": ["value", "confidence", "needs_confirmation"],
        },
        "teilnehmende_feuerwehrleute": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "confidence": {"type": "number"},
                "needs_confirmation": {"type": "boolean"},
            },
            "required": ["value", "confidence", "needs_confirmation"],
        },
        "bemerkungen": {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "confidence": {"type": "number"},
                "needs_confirmation": {"type": "boolean"},
            },
            "required": ["value", "confidence", "needs_confirmation"],
        },
    },
}


def _build_prompt(text: str) -> str:
    return f"""
Du extrahierst aus einer freien Antwort eines Feuerwehrangehörigen strukturierte Informationen
für einen Einsatzbericht.

Wichtige Regeln:
- Erfinde nichts.
- Trage nur Informationen ein, die explizit genannt oder sehr naheliegend gemeint sind.
- Wenn ein Feld nicht enthalten ist, lasse es ganz weg.
- Wenn etwas nicht sicher ist, setze needs_confirmation auf true.
- Datumsformat immer YYYY-MM-DD.
- Uhrzeit immer HH:MM im 24-Stunden-Format.
- Fahrzeuge kurz und normalisiert, z. B. "HLF 20", "LF 10", "DLK", "MZF".
- Keine zusätzlichen Felder erzeugen.

Aktuelles Referenzdatum für relative Angaben:
{CURRENT_REFERENCE_DATE}

Wichtige Datumsregel:
- Wenn der Nutzer "heute" sagt, ist das Datum {CURRENT_REFERENCE_DATE}.
- Relative Angaben wie "heute", "gestern", "morgen" müssen immer relativ zu diesem Referenzdatum aufgelöst werden.

Für "einsatzart" normalisiere sinnvoll:
- Autounfall, PKW-Unfall, LKW-Unfall, PKW gegen Baum, Auffahrunfall -> Verkehrsunfall
- Person eingeklemmt, Ölspur, Baum auf Straße, Türöffnung, THL -> Technische Hilfeleistung
- Zimmerbrand, Kellerbrand, Wohnhausbrand, Fahrzeugbrand, Rauchentwicklung -> Brandeinsatz

Wichtig:
- Wenn in der Antwort ein klarer Einsatz genannt wird, darf "einsatzart" nicht leer bleiben.
- Lieber einen sinnvollen Kandidaten liefern als leer lassen.

Antwort des Nutzers:
{text}
""".strip()


def _client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY ist nicht gesetzt.")
    return genai.Client(api_key=api_key)


def _status_from_confidence(
    confidence: float | None,
    needs_confirmation: bool,
) -> FieldStatus:
    if confidence is None:
        return FieldStatus.KANDIDAT
    if confidence >= 0.90 and not needs_confirmation:
        return FieldStatus.BESTAETIGT
    return FieldStatus.KANDIDAT


def _normalize_einsatzart(value: str) -> tuple[str, bool]:
    cleaned = value.strip()
    lowered = cleaned.lower()

    mapping = [
        (
            [
                "autounfall",
                "verkehrsunfall",
                "pkw-unfall",
                "lkw-unfall",
                "motorradunfall",
                "auffahrunfall",
                "pkw gegen",
                "fahrzeugunfall",
            ],
            "Verkehrsunfall",
            False,
        ),
        (
            [
                "person eingeklemmt",
                "eingeklemmt",
                "ölspur",
                "oelspur",
                "baum auf straße",
                "baum auf strasse",
                "türöffnung",
                "tueroeffnung",
                "technische hilfeleistung",
                "thl",
            ],
            "Technische Hilfeleistung",
            False,
        ),
        (
            [
                "zimmerbrand",
                "kellerbrand",
                "wohnhausbrand",
                "rauchentwicklung",
                "fahrzeugbrand",
                "brand",
                "brandeinsatz",
            ],
            "Brandeinsatz",
            False,
        ),
    ]

    for keywords, normalized, extra_confirmation in mapping:
        if any(keyword in lowered for keyword in keywords):
            return normalized, extra_confirmation

    return cleaned, True


def _scalar_update_from_payload(
    field_name: str,
    payload: dict[str, Any] | None,
    source_text: str,
) -> FieldUpdate[object] | None:
    if not payload:
        return None

    value = payload.get("value")
    if not isinstance(value, str):
        return None

    cleaned_value = value.strip()
    if not cleaned_value:
        return None

    confidence = payload.get("confidence")
    needs_confirmation = bool(payload.get("needs_confirmation", False))

    if field_name == "einsatzart":
        cleaned_value, extra_confirmation = _normalize_einsatzart(cleaned_value)
        needs_confirmation = needs_confirmation or extra_confirmation

    return FieldUpdate(
        value=cleaned_value,
        status=_status_from_confidence(confidence, needs_confirmation),
        confidence=confidence,
        source_text=source_text,
        needs_confirmation=needs_confirmation,
    )


def _list_update_from_payload(
    payload: dict[str, Any] | None,
    source_text: str,
) -> FieldUpdate[object] | None:
    if not payload:
        return None

    raw_value = payload.get("value")
    if not isinstance(raw_value, list):
        return None

    cleaned_list = [
        item.strip()
        for item in raw_value
        if isinstance(item, str) and item.strip()
    ]
    if not cleaned_list:
        return None

    confidence = payload.get("confidence")
    needs_confirmation = bool(payload.get("needs_confirmation", False))

    return FieldUpdate(
        value=cleaned_list,
        status=_status_from_confidence(confidence, needs_confirmation),
        confidence=confidence,
        source_text=source_text,
        needs_confirmation=needs_confirmation,
    )


def _fallback_extract_einsatzart_from_text(
    text: str,
) -> FieldUpdate[object] | None:
    lowered = text.lower()

    if any(
        keyword in lowered
        for keyword in [
            "autounfall",
            "verkehrsunfall",
            "pkw-unfall",
            "lkw-unfall",
            "motorradunfall",
            "auffahrunfall",
            "pkw gegen",
            "fahrzeugunfall",
        ]
    ):
        return FieldUpdate(
            value="Verkehrsunfall",
            status=FieldStatus.KANDIDAT,
            confidence=0.75,
            source_text=text,
            needs_confirmation=True,
        )

    if any(
        keyword in lowered
        for keyword in [
            "person eingeklemmt",
            "eingeklemmt",
            "ölspur",
            "oelspur",
            "baum auf straße",
            "baum auf strasse",
            "türöffnung",
            "tueroeffnung",
            "thl",
        ]
    ):
        return FieldUpdate(
            value="Technische Hilfeleistung",
            status=FieldStatus.KANDIDAT,
            confidence=0.75,
            source_text=text,
            needs_confirmation=True,
        )

    if any(
        keyword in lowered
        for keyword in [
            "zimmerbrand",
            "kellerbrand",
            "wohnhausbrand",
            "rauchentwicklung",
            "fahrzeugbrand",
            "brand",
        ]
    ):
        return FieldUpdate(
            value="Brandeinsatz",
            status=FieldStatus.KANDIDAT,
            confidence=0.75,
            source_text=text,
            needs_confirmation=True,
        )

    return None


def extract_updates_with_gemini(
    text: str,
    model_name: str = DEFAULT_GEMINI_MODEL,
) -> dict[str, FieldUpdate[object]]:
    cleaned_text = text.strip()
    if not cleaned_text:
        return {}

    client = _client()

    print("=== GEMINI REQUEST START ===")
    print("Model:", model_name)
    print("Text:", cleaned_text)
    print("============================")

    response = client.models.generate_content(
        model=model_name,
        contents=_build_prompt(cleaned_text),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=EXTRACTION_SCHEMA,
            temperature=0.1,
            thinking_config=types.ThinkingConfig(thinking_level="minimal"),
        ),
    )

    print("=== GEMINI REQUEST END ===")

    raw_text = (response.text or "").strip()
    print("=== GEMINI RAW RESPONSE ===")
    print(raw_text)
    print("===========================")

    if not raw_text:
        updates: dict[str, FieldUpdate[object]] = {}
        fallback_einsatzart = _fallback_extract_einsatzart_from_text(cleaned_text)
        if fallback_einsatzart is not None:
            updates["einsatzart"] = fallback_einsatzart
        return updates

    data = json.loads(raw_text)
    if not isinstance(data, dict):
        updates = {}
        fallback_einsatzart = _fallback_extract_einsatzart_from_text(cleaned_text)
        if fallback_einsatzart is not None:
            updates["einsatzart"] = fallback_einsatzart
        return updates

    print("=== GEMINI PARSED DATA ===")
    print(data)
    print("==========================")

    updates: dict[str, FieldUpdate[object]] = {}

    scalar_fields = [
        "einsatzart",
        "ort",
        "einsatzdatum",
        "einsatzuhrzeit",
        "bemerkungen",
    ]
    list_fields = [
        "fahrzeuge",
        "teilnehmende_feuerwehrleute",
    ]

    for field_name in scalar_fields:
        update = _scalar_update_from_payload(
            field_name,
            data.get(field_name),
            cleaned_text,
        )
        if update is not None:
            updates[field_name] = update

    for field_name in list_fields:
        update = _list_update_from_payload(data.get(field_name), cleaned_text)
        if update is not None:
            updates[field_name] = update

    if "einsatzart" not in updates:
        fallback_einsatzart = _fallback_extract_einsatzart_from_text(cleaned_text)
        if fallback_einsatzart is not None:
            updates["einsatzart"] = fallback_einsatzart

    return updates
