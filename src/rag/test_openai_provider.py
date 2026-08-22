from src.rag.openai_provider import (
    DEFAULT_MAX_OUTPUT_TOKENS,
    OpenAIProvider,
    OpenAIProviderUnavailableError,
    parse_max_output_tokens
)


class FakeOpenAIResponse:
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

        return FakeOpenAIResponse(self.output_text)


class FakeOpenAIClient:
    def __init__(self, output_text="Generated response", error=None):
        self.responses = FakeResponsesAPI(output_text, error=error)


def test_provider_accepts_injected_client():
    client = FakeOpenAIClient("Evidence answer")
    provider = OpenAIProvider(model="test-model", client=client)

    if provider.client is not client:
        raise ValueError("FAIL: OpenAI provider did not preserve injected client")

    print("PASS: OpenAI provider supports dependency-injected client")


def test_provider_calls_responses_api():
    client = FakeOpenAIClient("Evidence answer")
    provider = OpenAIProvider(model="test-model", client=client)

    result = provider.generate("System instructions", "User question")

    if result != "Evidence answer":
        raise ValueError("FAIL: OpenAI provider returned incorrect output")

    if len(client.responses.calls) != 1:
        raise ValueError("FAIL: OpenAI Responses API was not called exactly once")

    print("PASS: OpenAI provider uses Responses API")


def test_provider_sends_selected_model():
    client = FakeOpenAIClient()
    provider = OpenAIProvider(model="my-test-model", client=client)

    provider.generate("System", "User")

    call = client.responses.calls[0]

    if call["model"] != "my-test-model":
        raise ValueError("FAIL: OpenAI provider sent incorrect model")

    print("PASS: OpenAI provider sends configured model")


def test_provider_separates_system_and_user_prompts():
    client = FakeOpenAIClient()
    provider = OpenAIProvider(model="test-model", client=client)

    provider.generate("System grounding rules", "User research context")

    call = client.responses.calls[0]

    if call["instructions"] != "System grounding rules":
        raise ValueError("FAIL: OpenAI provider did not send system instructions correctly")

    if call["input"] != "User research context":
        raise ValueError("FAIL: OpenAI provider did not send user input correctly")

    print("PASS: OpenAI provider keeps instructions and user input separated")


def test_provider_disables_response_storage():
    client = FakeOpenAIClient()
    provider = OpenAIProvider(model="test-model", client=client)

    provider.generate("System", "User")

    call = client.responses.calls[0]

    if call.get("store") is not False:
        raise ValueError("FAIL: OpenAI provider did not explicitly disable response storage")

    print("PASS: OpenAI provider disables response storage")


def test_provider_sets_output_token_limit():
    client = FakeOpenAIClient()
    provider = OpenAIProvider(model="test-model", max_output_tokens=650, client=client)

    provider.generate("System", "User")

    call = client.responses.calls[0]

    if call.get("max_output_tokens") != 650:
        raise ValueError("FAIL: OpenAI provider sent incorrect output-token limit")

    print("PASS: OpenAI provider sends output-token limit")


def test_default_output_token_limit():
    provider = OpenAIProvider(model="test-model", client=FakeOpenAIClient())

    if provider.max_output_tokens != DEFAULT_MAX_OUTPUT_TOKENS:
        raise ValueError("FAIL: OpenAI provider returned incorrect default output-token limit")

    print("PASS: OpenAI provider uses bounded default output-token limit")


def test_parse_string_output_token_limit():
    result = parse_max_output_tokens("700")

    if result != 700:
        raise ValueError("FAIL: OpenAI output-token environment value was not parsed")

    print("PASS: OpenAI provider parses output-token environment values")


def test_invalid_output_token_limit_rejected():
    try:
        OpenAIProvider(model="test-model", max_output_tokens=20, client=FakeOpenAIClient())
    except ValueError:
        print("PASS: OpenAI provider rejects unsafe output-token limit")
        return

    raise ValueError("FAIL: Invalid OpenAI output-token limit was accepted")


def test_provider_strips_output():
    client = FakeOpenAIClient("   Trimmed response   ")
    provider = OpenAIProvider(model="test-model", client=client)

    result = provider.generate("System", "User")

    if result != "Trimmed response":
        raise ValueError("FAIL: OpenAI provider did not normalize output text")

    print("PASS: OpenAI provider normalizes response text")


def test_empty_output_rejected():
    client = FakeOpenAIClient("   ")
    provider = OpenAIProvider(model="test-model", client=client)

    try:
        provider.generate("System", "User")
    except OpenAIProviderUnavailableError:
        print("PASS: OpenAI provider rejects empty model output")
        return

    raise ValueError("FAIL: OpenAI provider accepted empty output")


def test_provider_error_is_sanitized():
    client = FakeOpenAIClient(error=RuntimeError("SECRET INTERNAL PROVIDER ERROR"))
    provider = OpenAIProvider(model="test-model", client=client)

    try:
        provider.generate("System", "User")
    except OpenAIProviderUnavailableError as error:
        if "SECRET INTERNAL PROVIDER ERROR" in str(error):
            raise ValueError("FAIL: Provider exception details leaked into public error")

        if str(error) != "OpenAI generation is temporarily unavailable":
            raise ValueError("FAIL: Provider returned unexpected sanitized error")

        print("PASS: OpenAI provider sanitizes upstream errors")
        return

    raise ValueError("FAIL: OpenAI provider error was not raised")


def test_invalid_system_prompt_rejected():
    provider = OpenAIProvider(model="test-model", client=FakeOpenAIClient())

    try:
        provider.generate("   ", "User")
    except ValueError:
        print("PASS: OpenAI provider rejects empty system prompt")
        return

    raise ValueError("FAIL: OpenAI provider accepted empty system prompt")


def test_invalid_user_prompt_rejected():
    provider = OpenAIProvider(model="test-model", client=FakeOpenAIClient())

    try:
        provider.generate("System", "   ")
    except ValueError:
        print("PASS: OpenAI provider rejects empty user prompt")
        return

    raise ValueError("FAIL: OpenAI provider accepted empty user prompt")


if __name__ == "__main__":
    test_provider_accepts_injected_client()
    test_provider_calls_responses_api()
    test_provider_sends_selected_model()
    test_provider_separates_system_and_user_prompts()
    test_provider_disables_response_storage()
    test_provider_sets_output_token_limit()
    test_default_output_token_limit()
    test_parse_string_output_token_limit()
    test_invalid_output_token_limit_rejected()
    test_provider_strips_output()
    test_empty_output_rejected()
    test_provider_error_is_sanitized()
    test_invalid_system_prompt_rejected()
    test_invalid_user_prompt_rejected()