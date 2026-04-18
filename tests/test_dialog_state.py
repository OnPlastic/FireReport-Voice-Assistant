from frva.dialog.state import DialogSession
from frva.model.report_schema import ReportState


def test_dialog_session_can_be_created() -> None:
    session = DialogSession()

    assert session is not None
    assert isinstance(session.report_state, ReportState)


def test_dialog_session_has_clean_default_values() -> None:
    session = DialogSession()

    assert session.started is False
    assert session.finished is False
    assert session.last_question is None


def test_dialog_session_start_sets_started_flag() -> None:
    session = DialogSession()

    session.start()

    assert session.started is True


def test_dialog_session_finish_sets_finished_flag() -> None:
    session = DialogSession()

    session.finish()

    assert session.finished is True


def test_dialog_session_set_last_question_stores_value() -> None:
    session = DialogSession()

    session.set_last_question("Wo war der Einsatz?")

    assert session.last_question == "Wo war der Einsatz?"


def test_dialog_session_reset_restores_default_state() -> None:
    session = DialogSession()

    session.start()
    session.finish()
    session.set_last_question("Was für ein Einsatz war das?")
    session.report_state.einsatzart.value = "Brand"

    session.reset()

    assert session.started is False
    assert session.finished is False
    assert session.last_question is None
    assert isinstance(session.report_state, ReportState)
    assert session.report_state.einsatzart.value is None