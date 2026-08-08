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

    assert "employees" in result.tables

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
    assert "employees" in result.tables

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

    assert result.tables == {"employees", "departments"}

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

    assert "employees" in result.tables
    assert "departments" in result.tables

def test_retrieve_preserves_relationship_between_tables():
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
        "Show me employee salary by department",
        schema,
        graph,
    )

    assert "employees" in result.tables
    assert "departments" in result.tables

    assert graph.has_edge("employees", "departments")

    edge_data = graph.get_edge_data("employees", "departments")
    edge = next(iter(edge_data.values()))

    assert edge["source_columns"] == ["department_id"]
    assert edge["target_columns"] == ["department_id"]

def test_retrieve_returns_relationships():
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
        "Show me employee salary by department",
        schema,
        graph,
    )

    assert "employees" in result.tables
    assert "departments" in result.tables

    assert len(result.relationships) == 1

    relationship = result.relationships[0]

    assert relationship.source_columns == ["department_id"]
    assert relationship.target_table == "departments"
    assert relationship.target_columns == ["department_id"]

def test_retrieve_related_tables_with_multiple_hops():
    sql = """
    CREATE TABLE locations (
        location_id INT PRIMARY KEY,
        city TEXT
    );

    CREATE TABLE departments (
        department_id INT PRIMARY KEY,
        name TEXT,
        location_id INT,
        FOREIGN KEY (location_id)
            REFERENCES locations(location_id)
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
        "Show me employee salary",
        schema,
        graph,
        max_hops=2,
    )

    assert result.tables == {
        "employees",
        "departments",
        "locations",
    }

def test_retrieve_related_tables_respects_max_hops():
    sql = """
    CREATE TABLE locations (
        location_id INT PRIMARY KEY,
        city TEXT
    );

    CREATE TABLE departments (
        department_id INT PRIMARY KEY,
        location_id INT,
        FOREIGN KEY (location_id)
            REFERENCES locations(location_id)
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
        "Show me employee salary",
        schema,
        graph,
        max_hops=1,
    )

    assert result.tables == {
        "employees",
        "departments"
    }

def test_retrieve_table_by_singular_name():
    sql = """
    CREATE TABLE employees (
        employee_id INT PRIMARY KEY
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    retriever = SchemaRetriever()

    result = retriever.retrieve(
        "Show me employee information",
        schema,
        graph,
    )

    assert "employees" in result.tables