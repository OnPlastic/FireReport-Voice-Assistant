"""Dialogzustand für den FRVA-MVP."""

from dataclasses import dataclass, field

from frva.model.report_schema import ReportState


@dataclass
class DialogSession:
    """Hält den aktuellen Zustand einer laufenden Dialogsitzung."""

    report_state: ReportState = field(default_factory=ReportState)
    started: bool = False
    finished: bool = False
    last_question: str | None = None

    def start(self) -> None:
        """Markiert die Sitzung als gestartet."""
        self.started = True

    def finish(self) -> None:
        """Markiert die Sitzung als abgeschlossen."""
        self.finished = True

    def set_last_question(self, question: str | None) -> None:
        """Speichert die zuletzt gestellte Frage."""
        self.last_question = question

    def reset(self) -> None:
        """Setzt die Sitzung vollständig zurück."""
        self.report_state = ReportState()
        self.started = False
        self.finished = False
        self.last_question = None