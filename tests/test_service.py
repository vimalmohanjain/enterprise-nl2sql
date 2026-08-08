from src.schema_graph.parser import SchemaParser
from src.schema_graph.service import NL2SQLService


class FakeLLMClient:
    def generate(self, prompt: str) -> str:
        return "SELECT * FROM employees"


def test_service_generates_sql():
    ddl = """
    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        name TEXT,
        salary REAL
    );
    """

    schema = SchemaParser().parse(ddl)

    service = NL2SQLService(
        client=FakeLLMClient(),
    )

    sql = service.generate(
        question="Show all employees",
        schema=schema,
    )

    assert sql == "SELECT * FROM employees"

class RecordingLLMClient:
    def __init__(self):
        self.prompt = None

    def generate(self, prompt: str) -> str:
        self.prompt = prompt
        return "SELECT salary FROM employees"


def test_service_uses_retrieved_schema_context():
    ddl = """
    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        salary REAL
    );

    CREATE TABLE products (
        product_id INT PRIMARY KEY,
        price REAL
    );
    """

    schema = SchemaParser().parse(ddl)

    client = RecordingLLMClient()

    service = NL2SQLService(client=client)

    service.generate(
        question="What is the salary?",
        schema=schema,
    )

    assert "Table: employees" in client.prompt
    assert "salary" in client.prompt

    # Unrelated schema should not reach the LLM.
    assert "Table: products" not in client.prompt