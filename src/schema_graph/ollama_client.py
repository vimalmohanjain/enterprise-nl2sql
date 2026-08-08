from typing import Any


class OllamaClient:
    """LLM client backed by the local Ollama API."""

    def __init__(
        self,
        http_client: Any,
        model: str,
        base_url: str = "http://localhost:11434",
    ):
        self._http_client = http_client
        self._model = model
        self._base_url = base_url

    def generate(self, prompt: str) -> str:
        try:
            response = self._http_client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                },
            )

            response.raise_for_status()

            data = response.json()

            return data["response"]

        except Exception as exc:
            raise RuntimeError("Ollama request failed") from exc