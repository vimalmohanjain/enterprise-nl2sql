from src.schema_graph.dataset import DatasetExample


def test_dataset_example_contains_question_and_sql():
    example = DatasetExample(
        question="Show employee names",
        sql="SELECT name FROM employees",
    )

    assert example.question == "Show employee names"
    assert example.sql == "SELECT name FROM employees"