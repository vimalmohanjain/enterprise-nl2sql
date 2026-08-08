from typing import Protocol


class LLMClient(Protocol):
    """Interface for an LLM capable of generating text."""

    def generate(self, prompt: str) -> str:
        """Generate text from a prompt."""
        ...


class NL2SQLGenerator:
    """Generate SQL using an LLM client."""

    def __init__(self, client: LLMClient):
        self.client = client

    def generate(self, prompt: str) -> str:
        return self.client.generate(prompt)