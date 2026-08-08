from src.schema_graph.ollama_client import OllamaClient
import pytest


class FakeResponse:
    def json(self):
        return {
            "response": "SELECT * FROM employees"
        }

    def raise_for_status(self):
        pass


class FakeHTTPClient:
    def __init__(self):
        self.url = None
        self.payload = None

    def post(self, url, json):
        self.url = url
        self.payload = json
        return FakeResponse()


def test_ollama_client_generates_sql():
    http_client = FakeHTTPClient()

    client = OllamaClient(
        http_client=http_client,
        model="test-model",
    )

    sql = client.generate(
        "Generate SQL for employees"
    )

    assert sql == "SELECT * FROM employees"


def test_ollama_client_passes_model_and_prompt():
    http_client = FakeHTTPClient()

    client = OllamaClient(
        http_client=http_client,
        model="qwen2.5-coder",
    )

    client.generate("Test prompt")

    assert http_client.payload["model"] == "qwen2.5-coder"
    assert http_client.payload["prompt"] == "Test prompt"
    assert http_client.payload["stream"] is False

class FailingResponse:
    def raise_for_status(self):
        raise Exception("Connection failed")

    def json(self):
        return {}


class FailingHTTPClient:
    def post(self, url, json):
        return FailingResponse()


def test_ollama_client_handles_request_failure():
    client = OllamaClient(
        http_client=FailingHTTPClient(),
        model="test-model",
    )

    with pytest.raises(
        RuntimeError,
        match="Ollama request failed",
    ):
        client.generate("Test prompt")

def test_ollama_client_uses_deterministic_temperature():
    http_client = FakeHTTPClient()

    client = OllamaClient(
        http_client=http_client,
        model="qwen2.5-coder:7b",
    )

    client.generate("Test prompt")

    assert http_client.payload["options"]["temperature"] == 0

