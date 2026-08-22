from src.rag.groq_provider import GroqProvider
from src.rag.openai_provider import OpenAIProvider

from src.rag.provider_factory import (
    DEFAULT_PROVIDER_NAME,
    get_default_llm_provider,
    normalize_provider_name
)


def test_default_provider_is_groq():
    if DEFAULT_PROVIDER_NAME != "groq":
        raise ValueError("FAIL: Free Groq provider is not the project default")

    print("PASS: Groq is the default live AI provider")


def test_factory_creates_groq_provider():
    provider = get_default_llm_provider(
        "groq"
    )

    if not isinstance(provider, GroqProvider):
        raise ValueError("FAIL: Provider factory did not create Groq provider")

    print("PASS: Provider factory creates Groq provider")


def test_factory_creates_openai_provider():
    provider = get_default_llm_provider(
        "openai"
    )

    if not isinstance(provider, OpenAIProvider):
        raise ValueError("FAIL: Provider factory did not preserve OpenAI support")

    print("PASS: Provider factory preserves OpenAI provider")


def test_provider_names_are_case_insensitive():
    provider = get_default_llm_provider(
        "  GrOq  "
    )

    if not isinstance(provider, GroqProvider):
        raise ValueError("FAIL: Provider factory did not normalize provider name")

    print("PASS: Provider factory normalizes provider names")


def test_unknown_provider_rejected():
    try:
        get_default_llm_provider(
            "unknown-provider"
        )

    except ValueError:
        print("PASS: Provider factory rejects unsupported provider")
        return

    raise ValueError("FAIL: Unsupported provider was accepted")


def test_empty_provider_name_rejected():
    try:
        normalize_provider_name(
            "   "
        )

    except ValueError:
        print("PASS: Provider factory rejects empty provider name")
        return

    raise ValueError("FAIL: Empty provider name was accepted")


if __name__ == "__main__":
    test_default_provider_is_groq()
    test_factory_creates_groq_provider()
    test_factory_creates_openai_provider()
    test_provider_names_are_case_insensitive()
    test_unknown_provider_rejected()
    test_empty_provider_name_rejected()