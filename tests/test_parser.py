from envguard.parser import parse


def values(text):
    return {e.key: e.value for e in parse(text).entries}


def test_basic_pairs_comments_and_blank_lines():
    text = "# comment\nA=1\n\nB = two \nexport C=3\n"
    assert values(text) == {"A": "1", "B": "two", "C": "3"}


def test_empty_value():
    assert values("A=\nB=''\n") == {"A": "", "B": ""}


def test_inline_comment_only_after_whitespace():
    assert values("A=value # note\nB=a#b\n") == {"A": "value", "B": "a#b"}


def test_quoted_values_keep_hash_and_spaces():
    assert values("A='x # y'\nB=\"  padded  \" # c\n") == {"A": "x # y", "B": "  padded  "}


def test_double_quote_escapes():
    assert values(r'A="line1\nline2 \"q\""') == {"A": 'line1\nline2 "q"'}


def test_single_quotes_are_literal():
    assert values(r"A='no\nescape'") == {"A": r"no\nescape"}


def test_equals_sign_inside_value():
    assert values("URL=postgres://u:p@h/db?a=b\n") == {"URL": "postgres://u:p@h/db?a=b"}


def test_errors_are_reported_with_line_numbers():
    result = parse("OK=1\nnot a pair\n9BAD=1\nQ=\"open\nR='x' junk\n")
    assert [line for line, _ in result.errors] == [2, 3, 4, 5]
    assert [e.key for e in result.entries] == ["OK"]


def test_directive_on_previous_line():
    entry = parse("# envguard: int optional\nPORT=\n").entries[0]
    assert entry.directives == ["int", "optional"]


def test_inline_directive():
    entry = parse("DEBUG=true # envguard: bool\n").entries[0]
    assert entry.directives == ["bool"]


def test_directive_survives_plain_comment_but_not_blank_line():
    text = "# envguard: int\n# the port\nA=1\n# envguard: bool\n\nB=1\n"
    a, b = parse(text).entries
    assert a.directives == ["int"]
    assert b.directives == []


def test_directive_applies_to_one_variable_only():
    a, b = parse("# envguard: int\nA=1\nB=2\n").entries
    assert a.directives == ["int"] and b.directives == []


def test_windows_line_endings():
    assert values("A=1\r\nB=2\r\n") == {"A": "1", "B": "2"}
