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
        response = self.client.generate(prompt)

        return self._clean_sql(response)

    def _clean_sql(self, response: str) -> str:
        sql = response.strip()

        if sql.startswith("```sql"):
            sql = sql[len("```sql"):]

        elif sql.startswith("```"):
            sql = sql[len("```"):]

        if sql.endswith("```"):
            sql = sql[:-3]

        sql = sql.strip()

        if not sql:
            raise ValueError("LLM returned an empty response")

        return sql