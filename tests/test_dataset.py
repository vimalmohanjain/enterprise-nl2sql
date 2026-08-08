from src.schema_graph.models import DatasetExample, DatabaseSchema, Table, Column
from src.schema_graph.dataset import DatasetGenerator
from src.schema_graph.parser import SchemaParser


def test_dataset_generator_creates_example_for_table():
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(name="employee_id", data_type="INT"),
                Column(name="name", data_type="TEXT"),
                Column(name="salary", data_type="REAL"),
            ],
        )
    )

    generator = DatasetGenerator()

    examples = generator.generate(schema)

    assert len(examples) >= 4
    assert any(
        example.question == "Show all employees"
        and example.sql == "SELECT * FROM employees"
        for example in examples
    )


def test_dataset_example_contains_question_and_sql():
    example = DatasetExample(
        question="Show employee names",
        sql="SELECT name FROM employees",
    )

    assert example.question == "Show employee names"
    assert example.sql == "SELECT name FROM employees"

def test_dataset_generator_creates_column_selection_example():
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(name="employee_id", data_type="INT"),
                Column(name="name", data_type="TEXT"),
                Column(name="salary", data_type="REAL"),
            ],
        )
    )

    generator = DatasetGenerator()

    examples = generator.generate(schema)

    assert any(
        example.question == "Show name from employees"
        and example.sql == "SELECT name FROM employees"
        for example in examples
    )

def test_dataset_generator_creates_multiple_column_example():
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(name="employee_id", data_type="INT"),
                Column(name="name", data_type="TEXT"),
                Column(name="salary", data_type="REAL"),
            ],
        )
    )

    generator = DatasetGenerator()

    examples = generator.generate(schema)

    assert any(
        example.sql == "SELECT name, salary FROM employees"
        for example in examples
    )

def test_dataset_generator_creates_filter_example():
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(name="employee_id", data_type="INT"),
                Column(name="salary", data_type="REAL"),
            ],
        )
    )

    generator = DatasetGenerator()

    examples = generator.generate(schema)

    assert any(
        example.sql == "SELECT * FROM employees WHERE salary > 50000"
        for example in examples
    )

def normalize_sql(sql: str) -> str:
    return " ".join(sql.split())

def test_dataset_generator_creates_join_example():
    sql = """
    CREATE TABLE departments (
        department_id INT PRIMARY KEY,
        name TEXT
    );

    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        name TEXT,
        department_id INT,
        FOREIGN KEY (department_id)
            REFERENCES departments(department_id)
    );
    """

    schema = SchemaParser().parse(sql)

    generator = DatasetGenerator()

    examples = generator.generate(schema)

    expected_sql = """
    SELECT employees.name, departments.name
    FROM employees
    JOIN departments
        ON employees.department_id = departments.department_id
    """.strip()

    assert any(
        normalize_sql(example.sql) == normalize_sql(expected_sql)
        for example in examples
    )

def test_dataset_generator_creates_count_example():
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(name="employee_id", data_type="INT"),
                Column(name="name", data_type="TEXT"),
            ],
        )
    )

    generator = DatasetGenerator()
    examples = generator.generate(schema)

    assert any(
        example.question == "How many employees are there?"
        and example.sql == "SELECT COUNT(*) FROM employees"
        for example in examples
    )

def test_dataset_generator_creates_average_example():
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(name="employee_id", data_type="INT"),
                Column(name="salary", data_type="REAL"),
            ],
        )
    )

    generator = DatasetGenerator()
    examples = generator.generate(schema)

    assert any(
        example.question == "What is the average salary of employees?"
        and example.sql == "SELECT AVG(salary) FROM employees"
        for example in examples
    )

def test_dataset_generator_does_not_average_primary_key():
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(
                    name="employee_id",
                    data_type="INT",
                    is_primary_key=True,
                ),
                Column(
                    name="salary",
                    data_type="REAL",
                ),
            ],
        )
    )

    generator = DatasetGenerator()
    examples = generator.generate(schema)

    assert not any(
        example.sql == "SELECT AVG(employee_id) FROM employees"
        for example in examples
    )

    assert any(
        example.sql == "SELECT AVG(salary) FROM employees"
        for example in examples
    )

def test_dataset_generator_creates_sum_min_max_examples():
    schema = DatabaseSchema()
    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(
                    name="employee_id",
                    data_type="INT",
                    is_primary_key=True,
                ),
                Column(
                    name="salary",
                    data_type="REAL",
                ),
            ],
        )
    )

    examples = DatasetGenerator().generate(schema)

    expected_sql = {
        "SELECT SUM(salary) FROM employees",
        "SELECT MIN(salary) FROM employees",
        "SELECT MAX(salary) FROM employees",
    }

    generated_sql = {example.sql for example in examples}

    assert expected_sql.issubset(generated_sql)


def test_dataset_generator_does_not_aggregate_primary_key():
    schema = DatabaseSchema()
    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(
                    name="employee_id",
                    data_type="INT",
                    is_primary_key=True,
                ),
                Column(
                    name="salary",
                    data_type="REAL",
                ),
            ],
        )
    )

    examples = DatasetGenerator().generate(schema)

    assert not any(
        example.sql in {
            "SELECT AVG(employee_id) FROM employees",
            "SELECT SUM(employee_id) FROM employees",
            "SELECT MIN(employee_id) FROM employees",
            "SELECT MAX(employee_id) FROM employees",
        }
        for example in examples
    )


def test_dataset_generator_creates_group_by_example():
    schema = DatabaseSchema()
    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(name="department_id", data_type="INT"),
                Column(name="salary", data_type="REAL"),
            ],
        )
    )

    examples = DatasetGenerator().generate(schema)

    assert any(
        example.sql
        == "SELECT department_id, AVG(salary) FROM employees GROUP BY department_id"
        for example in examples
    )

def test_dataset_generator_creates_order_by_limit_example():
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(
                    name="employee_id",
                    data_type="INT",
                    is_primary_key=True,
                ),
                Column(
                    name="salary",
                    data_type="REAL",
                ),
            ],
        )
    )

    examples = DatasetGenerator().generate(schema)

    assert any(
        example.sql
        == "SELECT * FROM employees ORDER BY salary DESC LIMIT 10"
        for example in examples
    )

def test_dataset_generator_creates_join_filter_example():
    sql = """
    CREATE TABLE departments (
        department_id INT PRIMARY KEY,
        name TEXT
    );

    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        name TEXT,
        salary REAL,
        department_id INT,
        FOREIGN KEY (department_id)
            REFERENCES departments(department_id)
    );
    """

    schema = SchemaParser().parse(sql)

    examples = DatasetGenerator().generate(schema)

    assert any(
        normalize_sql(example.sql)
        == normalize_sql(
            """
            SELECT employees.name, departments.name
            FROM employees
            JOIN departments
                ON employees.department_id = departments.department_id
            WHERE employees.salary > 50000
            """
        )
        for example in examples
    )

import json

def test_dataset_generator_exports_jsonl(tmp_path):
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(name="employee_id", data_type="INT"),
                Column(name="name", data_type="TEXT"),
            ],
        )
    )

    generator = DatasetGenerator()
    examples = generator.generate(schema)

    output_file = tmp_path / "dataset.jsonl"

    generator.export_jsonl(examples, output_file)

    lines = output_file.read_text(encoding="utf-8").splitlines()

    assert len(lines) == len(examples)

    first_record = json.loads(lines[0])

    assert "question" in first_record
    assert "sql" in first_record