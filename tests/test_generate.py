from envguard.checker import check
from envguard.generate import generate, infer
from envguard.parser import parse


def test_values_are_never_copied():
    text, count = generate("API_KEY=sk-live-123\nPASSWORD='hunter2'\n")
    assert count == 2
    assert "sk-live-123" not in text and "hunter2" not in text
    assert "API_KEY=\n" in text and "PASSWORD=\n" in text


def test_type_inference():
    assert infer("DEBUG", "true") == "bool"
    assert infer("PORT", "8000") == "port"
    assert infer("WORKERS", "4") == "int"
    assert infer("RATIO", "0.5") == "float"
    assert infer("DATABASE_URL", "postgres://u:p@h/db") == "url"
    assert infer("NAME", "hello") is None
    assert infer("SENTRY_DSN", "") == "optional"


def test_generated_example_validates_the_original_env():
    env = "DEBUG=true\nPORT=8000\nNAME=app\nSITE=https://example.com\nEMPTY=\n"
    example, _ = generate(env)
    assert check(example, env).findings == []


def test_duplicates_collapse_and_order_is_kept():
    text, count = generate("B=1\nA=2\nB=3\n")
    assert count == 2
    assert [e.key for e in parse(text).entries] == ["B", "A"]
