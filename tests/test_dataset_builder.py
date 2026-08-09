from src.schema_graph.dataset_builder import MultiSchemaDatasetBuilder


def test_builder_generates_examples_from_multiple_schemas(tmp_path):
    first_schema = tmp_path / "employees.sql"
    first_schema.write_text(
        """
        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY,
            name TEXT,
            salary INTEGER
        );
        """
    )

    second_schema = tmp_path / "products.sql"
    second_schema.write_text(
        """
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL
        );
        """
    )

    builder = MultiSchemaDatasetBuilder()

    examples = builder.build(tmp_path)

    questions = [example.question for example in examples]

    assert "Show all employees" in questions
    assert "Show all products" in questions

    assert len(examples) > 0

def test_builder_removes_duplicate_examples(tmp_path):
    first_schema = tmp_path / "first.sql"
    first_schema.write_text(
        """
        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY,
            name TEXT,
            salary INTEGER
        );
        """
    )

    second_schema = tmp_path / "second.sql"
    second_schema.write_text(
        """
        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY,
            name TEXT,
            salary INTEGER
        );
        """
    )

    builder = MultiSchemaDatasetBuilder()

    examples = builder.build(tmp_path)

    pairs = [
        (example.question, example.sql)
        for example in examples
    ]

    assert len(pairs) == len(set(pairs))