from src.rag.groq_provider import (
    DEFAULT_GROQ_MAX_OUTPUT_TOKENS,
    DEFAULT_GROQ_MODEL,
    GroqProvider,
    GroqProviderUnavailableError,
    parse_groq_max_output_tokens
)


class FakeGroqResponse:
    def __init__(self, output_text):
        self.output_text = output_text


class FakeResponsesAPI:
    def __init__(self, output_text="Generated response", error=None):
        self.output_text = output_text
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)

        if self.error is not None:
            raise self.error

        return FakeGroqResponse(self.output_text)


class FakeGroqClient:
    def __init__(self, output_text="Generated response", error=None):
        self.responses = FakeResponsesAPI(
            output_text=output_text,
            error=error
        )


def test_provider_accepts_injected_client():
    client = FakeGroqClient("Evidence answer")

    provider = GroqProvider(
        model="test-model",
        client=client
    )

    if provider.client is not client:
        raise ValueError("FAIL: Groq provider did not preserve injected client")

    print("PASS: Groq provider supports dependency-injected client")


def test_provider_calls_responses_api():
    client = FakeGroqClient("Evidence answer")

    provider = GroqProvider(
        model="test-model",
        client=client
    )

    result = provider.generate(
        "System instructions",
        "User question"
    )

    if result != "Evidence answer":
        raise ValueError("FAIL: Groq provider returned incorrect output")

    if len(client.responses.calls) != 1:
        raise ValueError("FAIL: Groq Responses API was not called exactly once")

    print("PASS: Groq provider uses Responses API")


def test_default_model():
    provider = GroqProvider(
        client=FakeGroqClient()
    )

    if provider.model != DEFAULT_GROQ_MODEL:
        raise ValueError("FAIL: Groq provider returned incorrect default model")

    print("PASS: Groq provider uses GPT-OSS 20B by default")


def test_provider_sends_selected_model():
    client = FakeGroqClient()

    provider = GroqProvider(
        model="custom-test-model",
        client=client
    )

    provider.generate(
        "System",
        "User"
    )

    call = client.responses.calls[0]

    if call["model"] != "custom-test-model":
        raise ValueError("FAIL: Groq provider sent incorrect model")

    print("PASS: Groq provider sends configured model")


def test_provider_separates_system_and_user_prompts():
    client = FakeGroqClient()

    provider = GroqProvider(
        model="test-model",
        client=client
    )

    provider.generate(
        "System grounding rules",
        "User research context"
    )

    call = client.responses.calls[0]

    if call["instructions"] != "System grounding rules":
        raise ValueError("FAIL: Groq provider did not send system instructions correctly")

    if call["input"] != "User research context":
        raise ValueError("FAIL: Groq provider did not send user input correctly")

    print("PASS: Groq provider separates instructions and user input")


def test_provider_sets_output_token_limit():
    client = FakeGroqClient()

    provider = GroqProvider(
        model="test-model",
        max_output_tokens=650,
        client=client
    )

    provider.generate(
        "System",
        "User"
    )

    call = client.responses.calls[0]

    if call.get("max_output_tokens") != 650:
        raise ValueError("FAIL: Groq provider sent incorrect output-token limit")

    print("PASS: Groq provider sends bounded output-token limit")


def test_provider_does_not_send_store_parameter():
    client = FakeGroqClient()

    provider = GroqProvider(
        model="test-model",
        client=client
    )

    provider.generate(
        "System",
        "User"
    )

    call = client.responses.calls[0]

    if "store" in call:
        raise ValueError("FAIL: Groq provider sent unsupported store parameter")

    print("PASS: Groq provider avoids beta store compatibility issue")


def test_default_output_token_limit():
    provider = GroqProvider(
        model="test-model",
        client=FakeGroqClient()
    )

    if provider.max_output_tokens != DEFAULT_GROQ_MAX_OUTPUT_TOKENS:
        raise ValueError("FAIL: Groq provider returned incorrect default output-token limit")

    print("PASS: Groq provider uses bounded default output-token limit")


def test_string_output_token_limit_is_parsed():
    result = parse_groq_max_output_tokens("700")

    if result != 700:
        raise ValueError("FAIL: Groq output-token string was not parsed")

    print("PASS: Groq provider parses output-token environment values")


def test_invalid_output_token_limit_rejected():
    try:
        GroqProvider(
            model="test-model",
            max_output_tokens=20,
            client=FakeGroqClient()
        )

    except ValueError:
        print("PASS: Groq provider rejects invalid output-token limit")
        return

    raise ValueError("FAIL: Invalid Groq output-token limit was accepted")


def test_provider_strips_output():
    client = FakeGroqClient(
        "   Trimmed response   "
    )

    provider = GroqProvider(
        model="test-model",
        client=client
    )

    result = provider.generate(
        "System",
        "User"
    )

    if result != "Trimmed response":
        raise ValueError("FAIL: Groq provider did not normalize output text")

    print("PASS: Groq provider normalizes response text")


def test_empty_output_rejected():
    client = FakeGroqClient("   ")

    provider = GroqProvider(
        model="test-model",
        client=client
    )

    try:
        provider.generate(
            "System",
            "User"
        )

    except GroqProviderUnavailableError:
        print("PASS: Groq provider rejects empty model output")
        return

    raise ValueError("FAIL: Groq provider accepted empty output")


def test_provider_error_is_sanitized():
    client = FakeGroqClient(
        error=RuntimeError(
            "SECRET INTERNAL GROQ ERROR"
        )
    )

    provider = GroqProvider(
        model="test-model",
        client=client
    )

    try:
        provider.generate(
            "System",
            "User"
        )

    except GroqProviderUnavailableError as error:
        if "SECRET INTERNAL GROQ ERROR" in str(error):
            raise ValueError("FAIL: Groq upstream exception leaked")

        if str(error) != "Groq generation is temporarily unavailable":
            raise ValueError("FAIL: Groq returned unexpected sanitized error")

        print("PASS: Groq provider sanitizes upstream errors")
        return

    raise ValueError("FAIL: Groq provider error was not raised")


def test_invalid_system_prompt_rejected():
    provider = GroqProvider(
        model="test-model",
        client=FakeGroqClient()
    )

    try:
        provider.generate(
            "   ",
            "User"
        )

    except ValueError:
        print("PASS: Groq provider rejects empty system prompt")
        return

    raise ValueError("FAIL: Groq provider accepted empty system prompt")


def test_invalid_user_prompt_rejected():
    provider = GroqProvider(
        model="test-model",
        client=FakeGroqClient()
    )

    try:
        provider.generate(
            "System",
            "   "
        )

    except ValueError:
        print("PASS: Groq provider rejects empty user prompt")
        return

    raise ValueError("FAIL: Groq provider accepted empty user prompt")


if __name__ == "__main__":
    test_provider_accepts_injected_client()
    test_provider_calls_responses_api()
    test_default_model()
    test_provider_sends_selected_model()
    test_provider_separates_system_and_user_prompts()
    test_provider_sets_output_token_limit()
    test_provider_does_not_send_store_parameter()
    test_default_output_token_limit()
    test_string_output_token_limit_is_parsed()
    test_invalid_output_token_limit_rejected()
    test_provider_strips_output()
    test_empty_output_rejected()
    test_provider_error_is_sanitized()
    test_invalid_system_prompt_rejected()
    test_invalid_user_prompt_rejected()