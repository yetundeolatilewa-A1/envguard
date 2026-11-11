import pytest

from envguard.rules import parse_rule, validate


def rule(*tokens):
    return parse_rule(list(tokens))


def test_defaults():
    r = rule()
    assert r.required and r.type is None and r.choices is None and not r.problems


def test_optional_and_required():
    assert not rule("optional").required
    assert rule("optional", "required").required


def test_choices_parsed():
    assert rule("choices=dev|staging|prod").choices == ["dev", "staging", "prod"]


@pytest.mark.parametrize("token", ["inty", "choices=", "REQUIRED"])
def test_bad_directives_are_reported(token):
    assert rule(token).problems


def test_conflicting_types_reported():
    assert rule("int", "bool").problems


@pytest.mark.parametrize(
    "kind,good,bad",
    [
        ("int", ["0", "42", "-7", "+3"], ["4.2", "abc", "1_000", " 5"]),
        ("float", ["1", "1.5", "-.5", "2e10", "3."], ["abc", "nan", "1.2.3"]),
        ("bool", ["true", "False", "1", "0", "yes", "NO", "on", "off"], ["maybe", "2", "tru"]),
        ("url", ["https://example.com/x", "postgres://u:p@h:5432/db", "sqlite:///db.sqlite3", "redis://localhost"], ["example.com", "http://", "just words"]),
        ("port", ["1", "8080", "65535"], ["0", "65536", "-1", "http"]),
    ],
)
def test_type_validators(kind, good, bad):
    r = rule(kind)
    for value in good:
        assert validate(value, r) is None, value
    for value in bad:
        assert validate(value, r), value


def test_choices_validator_lists_options_but_not_value():
    message = validate("secret-value", rule("choices=a|b"))
    assert "a, b" in message and "secret-value" not in message


def test_messages_never_contain_the_value():
    for kind in ("int", "float", "bool", "url", "port"):
        assert "s3cr3t" not in validate("s3cr3t", rule(kind))
