from src.schema_graph.parser import SchemaParser
from src.schema_graph.retriever import SchemaRetriever
from src.schema_graph.graph_builder import GraphBuilder
from src.schema_graph.models import DatabaseSchema, Table, Column, ForeignKey


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

def test_retrieve_tracks_matching_columns():
    sql = """
    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        name TEXT,
        salary REAL
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    retriever = SchemaRetriever()

    result = retriever.retrieve(
        "What is the salary?",
        schema,
        graph,
    )

    assert result.columns == {
        "employees.salary"
    }

def test_retrieve_tracks_matching_columns_across_tables():
    sql = """
    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        salary REAL
    );

    CREATE TABLE departments (
        department_id INT PRIMARY KEY,
        department_name TEXT
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    result = SchemaRetriever().retrieve(
        "Show salary and department_name",
        schema,
        graph,
    )

    assert result.columns == {
        "employees.salary",
        "departments.department_name",
    }

def test_retrieve_includes_relationship_columns():
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

    result = SchemaRetriever().retrieve(
        "Show employee salary",
        schema,
        graph,
    )

    assert result.columns == {
        "employees.salary",
        "employees.department_id",
        "departments.department_id",
    }

def test_retriever_expands_reverse_foreign_key_relationship():
    schema = DatabaseSchema()

    movies = Table(
        name="movies",
        columns=[
            Column(
                name="movie_id",
                data_type="integer",
                is_primary_key=True,
            ),
            Column(
                name="movie_title",
                data_type="text",
            ),
        ],
    )

    ratings = Table(
        name="ratings",
        columns=[
            Column(
                name="rating_id",
                data_type="integer",
                is_primary_key=True,
            ),
            Column(
                name="movie_id",
                data_type="integer",
                is_foreign_key=True,
            ),
        ],
        foreign_keys=[
            ForeignKey(
                source_columns=["movie_id"],
                target_table="movies",
                target_columns=["movie_id"],
            )
        ],
    )

    schema.add_table(movies)
    schema.add_table(ratings)

    graph = GraphBuilder().build(schema)

    result = SchemaRetriever().retrieve(
        question="Show movie titles",
        schema=schema,
        graph=graph,
        max_hops=1,
    )

    assert "movies" in result.tables
    assert "ratings" in result.tables