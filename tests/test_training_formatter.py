from src.schema_graph.models import DatasetExample
from training.formatter import TrainingFormatter


def test_training_formatter_creates_instruction_example():
    example = DatasetExample(
        question="Show employee names",
        sql="SELECT name FROM employees",
    )

    formatter = TrainingFormatter()

    result = formatter.format(example)

    assert result["instruction"] == "Show employee names"
    assert result["output"] == "SELECT name FROM employees"

def test_training_formatter_includes_schema_context():
    example = DatasetExample(
        question="Show employee names",
        sql="SELECT name FROM employees",
    )

    formatter = TrainingFormatter()

    result = formatter.format(
        example,
        schema_context=(
            "Table: employees\n"
            "Columns:\n"
            "- employee_id INT PRIMARY KEY\n"
            "- name TEXT"
        ),
    )

    assert "schema_context" in result
    assert "Table: employees" in result["schema_context"]
    assert result["instruction"] == "Show employee names"
    assert result["output"] == "SELECT name FROM employees"

def test_training_formatter_builds_training_text():
    example = DatasetExample(
        question="Show employee names",
        sql="SELECT name FROM employees",
    )

    formatter = TrainingFormatter()

    result = formatter.format(
        example,
        schema_context=(
            "Table: employees\n"
            "Columns:\n"
            "- employee_id INT PRIMARY KEY\n"
            "- name TEXT"
        ),
    )

    text = result["text"]

    assert "Table: employees" in text
    assert "Show employee names" in text
    assert "SELECT name FROM employees" in text
    assert "Generate SQL only." in text