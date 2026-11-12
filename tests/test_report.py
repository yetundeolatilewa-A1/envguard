import json

from envguard.checker import check
from envguard.report import format_json, format_text


def test_text_ok():
    assert format_text(check("A=\n", "A=1\n")) == "OK"


def test_text_ok_with_warning():
    out = format_text(check("A=\n", "A=1\nB=2\n"))
    assert out.splitlines()[-1] == "OK with 1 warning"
    assert "ENV004" in out and "B: not declared" in out


def test_text_failed_with_counts():
    out = format_text(check("A=\nB=\n", "C=1\n"))
    assert out.splitlines()[-1] == "FAILED: 2 errors, 1 warning"


def test_quiet_prints_only_summary():
    assert format_text(check("A=\n", ""), quiet=True) == "FAILED: 1 error"


def test_json_structure():
    data = json.loads(format_json(check("A=\n", "")))
    assert data["ok"] is False and data["errors"] == 1
    assert data["findings"][0]["code"] == "ENV001"
    assert data["findings"][0]["key"] == "A"
