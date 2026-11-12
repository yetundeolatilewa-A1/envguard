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


def test_config_supplies_paths_and_strict(project, capsys):
    (project / "ci.env").write_text("PORT=80\nNAME=x\nEXTRA=1\n")
    (project / "pyproject.toml").write_text('[tool.envguard]\nenv = "ci.env"\nstrict = true\n')
    assert main(["check"]) == 1
    out = capsys.readouterr().out
    assert "ci.env" in out and "ENV004" in out


def test_command_line_beats_config(project, capsys):
    (project / ".env").write_text("PORT=80\nNAME=x\n")
    (project / "ci.env").write_text("PORT=abc\n")
    (project / "pyproject.toml").write_text('[tool.envguard]\nenv = "ci.env"\n')
    assert main(["check"]) == 1
    assert main(["check", "--env", ".env"]) == 0


def test_ignore_from_config_and_flag(project, capsys):
    (project / ".env").write_text("PORT=80\nNAME=x\nA=1\nB=2\n")
    (project / "pyproject.toml").write_text('[tool.envguard]\nignore = ["A"]\nstrict = true\n')
    assert main(["check"]) == 1
    assert "B: not declared" in capsys.readouterr().out
    assert main(["check", "--ignore", "B"]) == 0


def test_explicit_config_file(project, capsys):
    (project / ".env").write_text("PORT=80\nNAME=x\nEXTRA=1\n")
    (project / "strict.toml").write_text("[tool.envguard]\nstrict = true\n")
    assert main(["check"]) == 0
    assert main(["check", "--config", "strict.toml"]) == 1


def test_bad_config_is_exit_2(project, capsys):
    (project / ".env").write_text("PORT=80\nNAME=x\n")
    (project / "pyproject.toml").write_text("[tool.envguard]\nnope = 1\n")
    assert main(["check"]) == 2
    assert "unknown option" in capsys.readouterr().err


def test_generate_uses_config_paths(project, capsys):
    (project / "app.env").write_text("A=1\n")
    (project / "pyproject.toml").write_text('[tool.envguard]\nenv = "app.env"\nexample = "app.example"\n')
    assert main(["generate"]) == 0
    assert (project / "app.example").exists()
