"""Einfache CLI-Demo für den FRVA-MVP-Core."""

from frva.dialog.manager import process_turn, start_dialog
from frva.dialog.state import DialogSession
from frva.model.report_schema import FieldStatus, FieldUpdate
from frva.report.formatter import format_report_summary
from frva.report.generator import generate_report_text


def run_demo() -> None:
    """Führt einen einfachen Demo-Durchlauf des MVP-Cores aus."""
    session = DialogSession()

    print("FRVA MVP Demo")
    print("=============")

    question = start_dialog(session)
    if question is not None:
        print(f"Assistent: {question}")
    else:
        print("Assistent: Danke, der Bericht ist vollständig.")
        
    question = process_turn(
        session=session,
        user_transcript="Es war ein Brandeinsatz.",
        updates={
            "einsatzart": FieldUpdate(
                value="ein Brandeinsatz",
                status=FieldStatus.BESTAETIGT,
                source_text="Es war ein Brandeinsatz.",
            )
        },
    )
    print("Nutzer: Es war ein Brandeinsatz.")
    print(f"Assistent: {question}")

    question = process_turn(
        session=session,
        user_transcript="In Pegnitz.",
        updates={
            "ort": FieldUpdate(
                value="Pegnitz",
                status=FieldStatus.BESTAETIGT,
                source_text="In Pegnitz.",
            )
        },
    )
    print("Nutzer: In Pegnitz.")
    print(f"Assistent: {question}")

    question = process_turn(
        session=session,
        user_transcript="Am 18.04.2026 gegen 19:30 Uhr.",
        updates={
            "einsatzdatum": FieldUpdate(
                value="2026-04-18",
                status=FieldStatus.BESTAETIGT,
                source_text="Am 18.04.2026",
            ),
            "einsatzuhrzeit": FieldUpdate(
                value="19:30",
                status=FieldStatus.BESTAETIGT,
                source_text="gegen 19:30 Uhr",
            ),
        },
    )
    print("Nutzer: Am 18.04.2026 gegen 19:30 Uhr.")
    print(f"Assistent: {question}")

    question = process_turn(
        session=session,
        user_transcript="Mit LF 10 und MZF.",
        updates={
            "fahrzeuge": FieldUpdate(
                value=["LF 10", "MZF"],
                status=FieldStatus.BESTAETIGT,
                source_text="Mit LF 10 und MZF.",
            )
        },
    )
    print("Nutzer: Mit LF 10 und MZF.")
    print(f"Assistent: {question}")

    question = process_turn(
        session=session,
        user_transcript="Max Mustermann und Erika Musterfrau.",
        updates={
            "teilnehmende_feuerwehrleute": FieldUpdate(
                value=["Max Mustermann", "Erika Musterfrau"],
                status=FieldStatus.BESTAETIGT,
                source_text="Max Mustermann und Erika Musterfrau.",
            )
        },
    )
    print("Nutzer: Max Mustermann und Erika Musterfrau.")
    print(f"Assistent: {question}")

    question = process_turn(
        session=session,
        user_transcript="Keine Besonderheiten.",
        updates={
            "bemerkungen": FieldUpdate(
                value="Keine Besonderheiten",
                status=FieldStatus.BESTAETIGT,
                source_text="Keine Besonderheiten.",
            )
        },
    )
    print("Nutzer: Keine Besonderheiten.")
    print(f"Assistent: {question}")

    print("\n--- Zusammenfassung ---")
    print(format_report_summary(session.report_state))

    print("\n--- Bericht ---")
    print(generate_report_text(session.report_state))


if __name__ == "__main__":
    run_demo()