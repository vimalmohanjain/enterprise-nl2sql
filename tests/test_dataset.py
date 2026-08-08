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