import os


DEFAULT_PROVIDER_NAME = "groq"


def normalize_provider_name(provider_name):
    if not isinstance(provider_name, str):
        raise ValueError("Provider name must be a string")

    normalized = provider_name.strip().casefold()

    if not normalized:
        raise ValueError("Provider name cannot be empty")

    return normalized


def get_default_llm_provider(provider_name=None):
    selected_provider = provider_name or os.getenv("AI_FITNESS_LLM_PROVIDER") or DEFAULT_PROVIDER_NAME

    selected_provider = normalize_provider_name(selected_provider)

    if selected_provider == "groq":
        from src.rag.groq_provider import GroqProvider

        return GroqProvider()

    if selected_provider == "openai":
        from src.rag.openai_provider import OpenAIProvider

        return OpenAIProvider()

    raise ValueError(f"Unsupported LLM provider: {selected_provider}")