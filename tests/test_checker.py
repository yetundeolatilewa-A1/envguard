from envguard.checker import check

EXAMPLE = """\
# envguard: url
DATABASE_URL=
# envguard: port
PORT=8000
# envguard: bool
DEBUG=false
# envguard: choices=dev|prod
APP_ENV=dev
# envguard: optional
SENTRY_DSN=
"""

GOOD = "DATABASE_URL=postgres://u:p@localhost/db\nPORT=8000\nDEBUG=true\nAPP_ENV=prod\n"


def codes(report):
    return [(f.code, f.key) for f in report.findings]


def test_good_env_passes():
    report = check(EXAMPLE, GOOD)
    assert report.ok and report.findings == []


def test_missing_required_variable():
    report = check(EXAMPLE, "PORT=1\nDEBUG=true\nAPP_ENV=dev\n")
    assert ("ENV001", "DATABASE_URL") in codes(report)
    assert not report.ok


def test_optional_may_be_missing_or_empty():
    assert check(EXAMPLE, GOOD).ok
    assert check(EXAMPLE, GOOD + "SENTRY_DSN=\n").findings == []


def test_empty_required_variable():
    report = check(EXAMPLE, GOOD.replace("PORT=8000", "PORT="))
    assert codes(report) == [("ENV002", "PORT")]


def test_wrong_type_and_bad_choice():
    env = "DATABASE_URL=nope\nPORT=abc\nDEBUG=true\nAPP_ENV=qa\n"
    assert codes(check(EXAMPLE, env)) == [
        ("ENV003", "DATABASE_URL"),
        ("ENV003", "PORT"),
        ("ENV003", "APP_ENV"),
    ]


def test_type_errors_do_not_leak_values():
    report = check(EXAMPLE, "DATABASE_URL=hunter2\nPORT=hunter2\nDEBUG=true\nAPP_ENV=dev\n")
    assert all("hunter2" not in f.message for f in report.findings)


def test_undeclared_variable_is_a_warning():
    report = check(EXAMPLE, GOOD + "EXTRA=1\n")
    assert report.ok and report.warnings == 1
    assert codes(report) == [("ENV004", "EXTRA")]


def test_strict_turns_warnings_into_errors():
    report = check(EXAMPLE, GOOD + "EXTRA=1\n", strict=True)
    assert not report.ok and report.errors == 1 and report.warnings == 0


def test_duplicate_keys_warn_and_last_wins():
    report = check(EXAMPLE, GOOD + "PORT=abc\n")
    assert ("ENV005", "PORT") in codes(report)
    assert ("ENV003", "PORT") in codes(report)


def test_bad_directive_in_example():
    report = check("# envguard: integer\nA=1\n", "A=1\n")
    assert codes(report) == [("ENV006", "A")]


def test_unparsable_lines_in_either_file():
    report = check("A=1\noops\n", "A=1\nalso oops\n")
    assert [(f.code, f.file) for f in report.findings] == [
        ("ENV007", ".env.example"),
        ("ENV007", ".env"),
    ]


def test_file_names_appear_in_findings():
    report = check("A=\n", "", example_name="ex.txt", env_name="real.env")
    assert report.findings[0].file == "real.env"
    assert "ex.txt:1" in report.findings[0].message


def test_ignore_silences_undeclared_warning():
    report = check(EXAMPLE, GOOD + "EXTRA=1\nOTHER=2\n", ignore=["EXTRA"])
    assert codes(report) == [("ENV004", "OTHER")]
