import json

import pytest

from envguard.cli import main

EXAMPLE = "# envguard: port\nPORT=8000\nNAME=\n"


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env.example").write_text(EXAMPLE)
    return tmp_path


def test_check_passes(project, capsys):
    (project / ".env").write_text("PORT=80\nNAME=x\n")
    assert main(["check"]) == 0
    assert capsys.readouterr().out.strip() == "OK"


def test_check_fails_with_exit_1(project, capsys):
    (project / ".env").write_text("PORT=abc\n")
    assert main(["check"]) == 1
    out = capsys.readouterr().out
    assert "ENV003" in out and "ENV001" in out and "FAILED: 2 errors" in out


def test_strict_flag(project, capsys):
    (project / ".env").write_text("PORT=80\nNAME=x\nEXTRA=1\n")
    assert main(["check"]) == 0
    assert main(["check", "--strict"]) == 1


def test_json_format(project, capsys):
    (project / ".env").write_text("PORT=80\n")
    assert main(["check", "--format", "json"]) == 1
    assert json.loads(capsys.readouterr().out)["findings"][0]["code"] == "ENV001"


def test_custom_paths(project, capsys):
    (project / "ci.env").write_text("PORT=1\nNAME=n\n")
    assert main(["check", "--env", "ci.env", "--example", ".env.example"]) == 0


def test_missing_file_is_exit_2(project, capsys):
    assert main(["check"]) == 2
    assert "file not found: .env" in capsys.readouterr().err


def test_generate_writes_file_and_refuses_overwrite(project, capsys):
    (project / ".env").write_text("PORT=80\nSECRET=abc123\n")
    assert main(["generate", "--output", "out.example"]) == 0
    written = (project / "out.example").read_text()
    assert "SECRET=\n" in written and "abc123" not in written
    assert main(["generate", "--output", "out.example"]) == 2
    assert main(["generate", "--output", "out.example", "--force"]) == 0


def test_generate_to_stdout(project, capsys):
    (project / ".env").write_text("A=1\n")
    assert main(["generate", "--output", "-"]) == 0
    assert "A=\n" in capsys.readouterr().out


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "envguard" in capsys.readouterr().out


def test_subcommand_required():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2
