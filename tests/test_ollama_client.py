from src.schema_graph.ollama_client import OllamaClient


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