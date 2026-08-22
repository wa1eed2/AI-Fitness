from abc import ABC, abstractmethod


class LLMProviderUnavailableError(RuntimeError):
    pass


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt, user_prompt):
        raise NotImplementedError