from src.schema_graph.parser import SchemaParser
from src.schema_graph.retriever import SchemaRetriever
from src.schema_graph.graph_builder import GraphBuilder


def test_retrieve_table_by_name():
    sql = """
    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        name TEXT,
        salary REAL
    );

    CREATE TABLE departments (
        department_id INT PRIMARY KEY,
        name TEXT
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    retriever = SchemaRetriever()
    result = retriever.retrieve("Show me employees", schema, graph)

    assert "employees" in result

def test_retrieve_table_by_column_name():
    sql = """
    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        name TEXT,
        salary REAL
    );

    CREATE TABLE departments (
        department_id INT PRIMARY KEY,
        name TEXT
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    retriever = SchemaRetriever()
    result = retriever.retrieve("What is the salary?", schema, graph)
    print(result)
    assert "employees" in result

def test_retrieve_multiple_tables_by_columns():
    sql = """
    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        name TEXT,
        salary REAL,
        department_id INT
    );

    CREATE TABLE departments (
        department_id INT PRIMARY KEY,
        name TEXT
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    retriever = SchemaRetriever()
    result = retriever.retrieve(
        "Show employee salary and department name",
        schema,
        graph
    )

    assert result == {"employees", "departments"}

def test_retrieve_related_table_through_foreign_key():
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
    result = retriever.retrieve("Show me employee salary", schema, graph)

    assert "employees" in result
    assert "departments" in result