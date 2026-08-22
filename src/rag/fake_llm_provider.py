from src.rag.llm_provider import (
    LLMProvider
)


class FakeLLMProvider(
    LLMProvider
):
    def __init__(
        self,
        response
    ):
        if not isinstance(response, str):
            raise ValueError("Fake LLM response must be a string")

        self.response = response
        self.calls = []


    def generate(
        self,
        system_prompt,
        user_prompt
    ):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt
            }
        )

        return self.response