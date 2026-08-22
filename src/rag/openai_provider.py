import os

from src.rag.llm_provider import (
    LLMProvider,
    LLMProviderUnavailableError
)


DEFAULT_OPENAI_MODEL = "gpt-5.6"
DEFAULT_MAX_OUTPUT_TOKENS = 800
MIN_MAX_OUTPUT_TOKENS = 100
MAX_MAX_OUTPUT_TOKENS = 4000


class OpenAIProviderUnavailableError(LLMProviderUnavailableError):
    pass


def parse_max_output_tokens(value):
    if value is None:
        return DEFAULT_MAX_OUTPUT_TOKENS

    if isinstance(value, bool):
        raise ValueError("OpenAI max_output_tokens must be an integer")

    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("OpenAI max_output_tokens must be an integer") from error

    if parsed < MIN_MAX_OUTPUT_TOKENS or parsed > MAX_MAX_OUTPUT_TOKENS:
        raise ValueError(f"OpenAI max_output_tokens must be between {MIN_MAX_OUTPUT_TOKENS} and {MAX_MAX_OUTPUT_TOKENS}")

    return parsed


class OpenAIProvider(LLMProvider):
    def __init__(self, model=None, max_output_tokens=None, client=None):
        selected_model = model or os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL

        if not isinstance(selected_model, str):
            raise ValueError("OpenAI model must be a string")

        selected_model = selected_model.strip()

        if not selected_model:
            raise ValueError("OpenAI model cannot be empty")

        configured_max_tokens = max_output_tokens

        if configured_max_tokens is None:
            configured_max_tokens = os.getenv("OPENAI_MAX_OUTPUT_TOKENS")

        self.model = selected_model
        self.max_output_tokens = parse_max_output_tokens(configured_max_tokens)
        self.client = client

    def get_client(self):
        if self.client is not None:
            return self.client

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise OpenAIProviderUnavailableError("OpenAI API access is not configured")

        try:
            from openai import OpenAI
        except ImportError as error:
            raise OpenAIProviderUnavailableError("The OpenAI Python package is not installed") from error

        self.client = OpenAI(api_key=api_key)

        return self.client

    def generate(self, system_prompt, user_prompt):
        if not isinstance(system_prompt, str) or not system_prompt.strip():
            raise ValueError("System prompt must be a non-empty string")

        if not isinstance(user_prompt, str) or not user_prompt.strip():
            raise ValueError("User prompt must be a non-empty string")

        client = self.get_client()

        try:
            response = client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=user_prompt,
                max_output_tokens=self.max_output_tokens,
                store=False
            )
        except Exception as error:
            raise OpenAIProviderUnavailableError("OpenAI generation is temporarily unavailable") from error

        output_text = getattr(response, "output_text", None)

        if not isinstance(output_text, str):
            raise OpenAIProviderUnavailableError("OpenAI response did not contain text output")

        output_text = output_text.strip()

        if not output_text:
            raise OpenAIProviderUnavailableError("OpenAI response contained empty text output")

        return output_text