"""has_openai_key must reject empties and the .env.example placeholder."""
from app.core.config import Settings


def test_missing_key_is_not_configured():
    assert Settings(openai_api_key="").has_openai_key is False


def test_placeholder_key_is_not_configured():
    # setup.sh recreates .env from .env.example, whose value is "sk-...".
    assert Settings(openai_api_key="sk-...").has_openai_key is False
    assert Settings(openai_api_key="sk-").has_openai_key is False


def test_short_or_test_key_is_not_configured():
    assert Settings(openai_api_key="sk-test-key").has_openai_key is False
    assert Settings(openai_api_key="sk-abc").has_openai_key is False


def test_realistic_key_is_configured():
    assert Settings(openai_api_key="sk-" + "a" * 40).has_openai_key is True
