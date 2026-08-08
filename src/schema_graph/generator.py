from typing import Protocol
import re


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
        response = self.client.generate(prompt)

        return self._clean_sql(response)

    def _clean_sql(self, response: str) -> str:
        sql = response.strip()

        fenced_match = re.search(
            r"```(?:sql)?\s*(.*?)```",
            sql,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if fenced_match:
            sql = fenced_match.group(1).strip()
        else:
            sql = sql.strip()

        if not sql:
            raise ValueError("LLM returned an empty response")

        return sql