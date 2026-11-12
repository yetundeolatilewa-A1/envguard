import pytest

from envguard.scan import find_usages, scan


def make(tmp_path, files):
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return tmp_path


def names(tmp_path, files):
    make(tmp_path, files)
    usages, _ = find_usages([tmp_path])
    return set(usages)


@pytest.mark.parametrize(
    "code,expected",
    [
        ('os.environ["A_KEY"]', {"A_KEY"}),
        ("os.environ['A_KEY']", {"A_KEY"}),
        ('os.environ.get("A_KEY", "x")', {"A_KEY"}),
        ('os.getenv("A_KEY")', {"A_KEY"}),
        ('from os import environ, getenv\nx = environ["A"] + getenv("B")', {"A", "B"}),
        ('os.environ.setdefault("A_KEY", "1")', {"A_KEY"}),
        ("os.environ[name]", set()),
        ('os.getenv(f"{x}_KEY")', set()),
        ('print("environ is a word")', set()),
    ],
)
def test_python_patterns(tmp_path, code, expected):
    assert names(tmp_path, {"app.py": code}) == expected


@pytest.mark.parametrize(
    "code,expected",
    [
        ("const a = process.env.API_URL;", {"API_URL"}),
        ('const a = process.env["API_URL"];', {"API_URL"}),
        ("const a = import.meta.env.VITE_KEY;", {"VITE_KEY"}),
        ("const a = process.env[name];", set()),
    ],
)
def test_javascript_patterns(tmp_path, code, expected):
    assert names(tmp_path, {"web/app.ts": code}) == expected


def test_reports_first_usage_location(tmp_path):
    make(tmp_path, {"a.py": 'import os\n\nx = os.getenv("K")\n', "b.py": 'os.getenv("K")\n'})
    usages, scanned = find_usages([tmp_path])
    assert scanned == 2
    assert (usages["K"].file.endswith("a.py"), usages["K"].line) == (True, 3)


def test_comment_lines_and_skipped_folders_are_ignored(tmp_path):
    found = names(
        tmp_path,
        {
            "app.py": '# os.getenv("COMMENTED")\nos.getenv("REAL")\n',
            "node_modules/pkg/index.js": "process.env.VENDORED",
            ".venv/lib/x.py": 'os.getenv("VENV")',
            "notes.txt": 'os.getenv("TEXT_FILE")',
        },
    )
    assert found == {"REAL"}


def test_explicit_file_path_is_scanned(tmp_path):
    make(tmp_path, {"weird.txt": 'os.getenv("X")'})
    usages, scanned = find_usages([tmp_path / "weird.txt"])
    assert set(usages) == {"X"} and scanned == 1


def test_missing_path_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_usages([tmp_path / "nope"])


EXAMPLE = "DATABASE_URL=\nSECRET_KEY=\nLEGACY=\n"


def usages_for(tmp_path, code):
    make(tmp_path, {"app.py": code})
    return find_usages([tmp_path])[0]


def test_undeclared_variable_is_a_warning(tmp_path):
    usages = usages_for(tmp_path, 'os.getenv("DATABASE_URL")\nos.getenv("NEW_THING")\n')
    report = scan(EXAMPLE, usages)
    assert [(f.code, f.key, f.line) for f in report.findings] == [("ENV101", "NEW_THING", 2)]
    assert report.ok


def test_strict_makes_it_an_error(tmp_path):
    usages = usages_for(tmp_path, 'os.getenv("NEW_THING")\n')
    assert not scan(EXAMPLE, usages, strict=True).ok


def test_system_variables_and_ignore_are_skipped(tmp_path):
    usages = usages_for(tmp_path, 'os.getenv("PATH")\nos.getenv("HOME")\nos.getenv("MINE")\n')
    assert scan(EXAMPLE, usages, ignore=["MINE"]).findings == []


def test_unused_is_opt_in(tmp_path):
    usages = usages_for(tmp_path, 'os.getenv("DATABASE_URL")\n')
    assert scan(EXAMPLE, usages).findings == []
    report = scan(EXAMPLE, usages, unused=True)
    assert [(f.code, f.key) for f in report.findings] == [("ENV102", "SECRET_KEY"), ("ENV102", "LEGACY")]
    assert scan(EXAMPLE, usages, unused=True, ignore=["LEGACY"]).warnings == 1


def test_example_syntax_errors_are_reported(tmp_path):
    report = scan("oops\n", {})
    assert [f.code for f in report.findings] == ["ENV007"]
