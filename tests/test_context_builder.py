from src.schema_graph.parser import SchemaParser
from src.schema_graph.graph_builder import GraphBuilder
from src.schema_graph.retriever import SchemaRetriever
from src.schema_graph.context_builder import ContextBuilder


def test_build_context_for_retrieved_tables():
    sql = """
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

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    retriever = SchemaRetriever()

    result = retriever.retrieve(
        "Show employee salary",
        schema,
        graph,
    )

    builder = ContextBuilder()

    context = builder.build(result, schema)

    assert "employees" in context.tables
    assert "departments" in context.tables

def test_context_contains_table_columns():
    sql = """
    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        salary REAL
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    retriever = SchemaRetriever()

    result = retriever.retrieve(
        "Show employee salary",
        schema,
        graph,
    )

    context = ContextBuilder().build(result, schema)

    employees = context.tables["employees"]

    assert employees.columns["employee_id"].data_type == "INT"
    assert employees.columns["salary"].data_type == "FLOAT"
    assert "employee_id" in employees.columns
    assert "salary" in employees.columns

def test_context_contains_relationships():
    sql = """
    CREATE TABLE departments (
        department_id INT PRIMARY KEY
    );

    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        department_id INT,
        FOREIGN KEY (department_id)
            REFERENCES departments(department_id)
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    retriever = SchemaRetriever()

    result = retriever.retrieve(
        "Show employee information",
        schema,
        graph,
    )

    # print("TABLES:", result.tables)
    # print("RELATIONSHIPS:", result.relationships)

    context = ContextBuilder().build(result, schema)

    assert len(context.relationships) == 1

    relationship = context.relationships[0]

    assert relationship.source_table == "employees"
    assert relationship.target_table == "departments"
    assert relationship.source_columns == ["department_id"]
    assert relationship.target_columns == ["department_id"]

def test_context_builder_builds_full_schema_context():
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

    context = ContextBuilder().build_full(schema)

    assert set(context.tables) == {
        "departments",
        "employees",
    }

    assert "salary" in context.tables["employees"].columns

    assert len(context.relationships) == 1

    relationship = context.relationships[0]

    assert relationship.source_table == "employees"
    assert relationship.target_table == "departments"

