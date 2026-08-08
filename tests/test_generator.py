from src.schema_graph.generator import NL2SQLGenerator


class FakeLLMClient:
    def generate(self, prompt: str) -> str:
        return "SELECT * FROM employees"


def test_generator_returns_sql_from_llm():
    client = FakeLLMClient()

    generator = NL2SQLGenerator(client)

    sql = generator.generate(
        "Generate SQL for employees"
    )

    assert sql == "SELECT * FROM employees"


def test_generator_passes_prompt_to_llm():
    class RecordingLLMClient:
        def __init__(self):
            self.prompt = None

        def generate(self, prompt: str) -> str:
            self.prompt = prompt
            return "SELECT * FROM employees"

    client = RecordingLLMClient()
    generator = NL2SQLGenerator(client)

    generator.generate("Test prompt")

from src.schema_graph.parser import SchemaParser
from src.schema_graph.graph_builder import GraphBuilder
from src.schema_graph.retriever import SchemaRetriever
from src.schema_graph.context_builder import ContextBuilder
from src.schema_graph.prompt_builder import PromptBuilder
from src.schema_graph.generator import NL2SQLGenerator


class RecordingLLMClient:
    def __init__(self):
        self.prompt = None

    def generate(self, prompt: str) -> str:
        self.prompt = prompt
        return (
            "SELECT employees.salary, departments.name "
            "FROM employees "
            "JOIN departments "
            "ON employees.department_id = departments.department_id"
        )


def test_end_to_end_pipeline_generates_sql():
    ddl = """
    CREATE TABLE departments (
        department_id INT PRIMARY KEY,
        name TEXT
    );

    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        salary REAL,
        department_id INT,
        FOREIGN KEY (department_id)
            REFERENCES departments(department_id)
    );
    """

    question = "Show employee salary by department"

    schema = SchemaParser().parse(ddl)
    graph = GraphBuilder().build(schema)

    retrieval = SchemaRetriever().retrieve(
        question,
        schema,
        graph,
    )

    context = ContextBuilder().build(
        retrieval,
        schema,
    )

    prompt = PromptBuilder().build(
        question,
        context,
    )

    client = RecordingLLMClient()
    generator = NL2SQLGenerator(client)

    sql = generator.generate(prompt)

    assert "SELECT" in sql
    assert "JOIN departments" in sql

    assert client.prompt == prompt
    assert "Table: employees" in client.prompt
    assert "Table: departments" in client.prompt
    assert (
        "employees.department_id -> departments.department_id"
        in client.prompt
    )