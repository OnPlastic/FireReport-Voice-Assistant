from frva.main import run_demo


def test_run_demo_prints_summary_and_report(capsys) -> None:
    run_demo()

    captured = capsys.readouterr()
    output = captured.out

    assert "FRVA MVP Demo" in output
    assert "--- Zusammenfassung ---" in output
    assert "--- Bericht ---" in output
    assert "Einsatzübersicht" in output
    assert "Pegnitz" in output
    assert "LF 10 und MZF" in output