import pytest

from envguard.config import ConfigError, load_config


def write(tmp_path, text, name="pyproject.toml"):
    path = tmp_path / name
    path.write_text(text)
    return path


def test_no_file_means_empty_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_config() == {}


def test_pyproject_without_our_table(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write(tmp_path, '[project]\nname = "x"\n')
    assert load_config() == {}


def test_reads_all_options(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write(
        tmp_path,
        '[tool.envguard]\nenv = ".env.ci"\nexample = "ex.txt"\nstrict = true\nignore = ["A", "B"]\n',
    )
    assert load_config() == {"env": ".env.ci", "example": "ex.txt", "strict": True, "ignore": ["A", "B"]}


def test_explicit_path(tmp_path):
    path = write(tmp_path, "[tool.envguard]\nstrict = true\n", "custom.toml")
    assert load_config(str(path)) == {"strict": True}


def test_explicit_missing_path_is_an_error(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(str(tmp_path / "nope.toml"))


def test_unknown_option_is_an_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write(tmp_path, "[tool.envguard]\nstrikt = true\n")
    with pytest.raises(ConfigError, match="strikt"):
        load_config()


@pytest.mark.parametrize(
    "body",
    ['env = 3', 'example = true', 'strict = "yes"', 'ignore = "A"', 'ignore = [1, 2]'],
)
def test_wrong_types_are_errors(tmp_path, monkeypatch, body):
    monkeypatch.chdir(tmp_path)
    write(tmp_path, f"[tool.envguard]\n{body}\n")
    with pytest.raises(ConfigError):
        load_config()


def test_invalid_toml_is_an_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write(tmp_path, "[tool.envguard\n")
    with pytest.raises(ConfigError, match="invalid TOML"):
        load_config()
