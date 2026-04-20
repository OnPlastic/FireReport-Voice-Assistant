from __future__ import annotations

from frva.nlp.gemini_extractor import extract_updates_with_gemini


def main() -> None:
    text = "Ein Wohnhausbrand in der Hauptstraße."
    updates = extract_updates_with_gemini(text)

    print("=== EXTRACTED UPDATES ===")
    for key, value in updates.items():
        print(key, "->", value)
    print("=========================")


if __name__ == "__main__":
    main()