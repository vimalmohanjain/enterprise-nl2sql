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

def test_retrieve_includes_bridge_table_between_relevant_tables():
    schema = DatabaseSchema()

    customers = Table(
        name="customers",
        columns=[
            Column(
                name="customer_id",
                data_type="integer",
                is_primary_key=True,
            ),
            Column(
                name="name",
                data_type="text",
            ),
        ],
    )

    transactions = Table(
        name="transactions",
        columns=[
            Column(
                name="transaction_id",
                data_type="integer",
                is_primary_key=True,
            ),
            Column(
                name="customer_id",
                data_type="integer",
                is_foreign_key=True,
            ),
        ],
        foreign_keys=[
            ForeignKey(
                source_columns=["customer_id"],
                target_table="customers",
                target_columns=["customer_id"],
            )
        ],
    )

    line_items = Table(
        name="line_items",
        columns=[
            Column(
                name="transaction_id",
                data_type="integer",
                is_foreign_key=True,
            ),
            Column(
                name="quantity",
                data_type="integer",
            ),
        ],
        foreign_keys=[
            ForeignKey(
                source_columns=["transaction_id"],
                target_table="transactions",
                target_columns=["transaction_id"],
            )
        ],
    )

    schema.add_table(customers)
    schema.add_table(transactions)
    schema.add_table(line_items)

    graph = GraphBuilder().build(schema)

    result = SchemaRetriever().retrieve(
        question="Show customers and line_items quantity",
        schema=schema,
        graph=graph,
        max_hops=0,
    )

    assert "customers" in result.tables
    assert "line_items" in result.tables

    # Not mentioned in the question; required only as the bridge.
    assert "transactions" in result.tables
    relationship_pairs = {
        (r.source_table, r.target_table)
        for r in result.relationships
    }

    assert ("transactions", "customers") in relationship_pairs
    assert ("line_items", "transactions") in relationship_pairs

def test_retrieve_matches_underscored_column_from_natural_language():
    schema = DatabaseSchema()

    business = Table(
        name="Business",
        columns=[
            Column(
                name="business_id",
                data_type="integer",
                is_primary_key=True,
            ),
            Column(
                name="city",
                data_type="text",
            ),
        ],
    )

    business_hours = Table(
        name="Business_Hours",
        columns=[
            Column(
                name="business_id",
                data_type="integer",
                is_foreign_key=True,
            ),
            Column(
                name="opening_time",
                data_type="text",
            ),
        ],
        foreign_keys=[
            ForeignKey(
                source_columns=["business_id"],
                target_table="Business",
                target_columns=["business_id"],
            )
        ],
    )

    schema.add_table(business)
    schema.add_table(business_hours)

    graph = GraphBuilder().build(schema)

    result = SchemaRetriever().retrieve(
        question="List the opening time for businesses in Anthem",
        schema=schema,
        graph=graph,
        max_hops=0,
    )

    assert "Business_Hours" in result.tables
    assert "Business_Hours.opening_time" in result.columns

def test_retrieve_matches_compound_table_words_anywhere_in_question():
    schema = DatabaseSchema()

    sales_in_weather = Table(
        name="sales_in_weather",
        columns=[
            Column(
                name="store_nbr",
                data_type="integer",
            ),
            Column(
                name="units",
                data_type="integer",
            ),
        ],
    )

    weather = Table(
        name="weather",
        columns=[
            Column(
                name="station_nbr",
                data_type="integer",
            ),
        ],
    )

    schema.add_table(sales_in_weather)
    schema.add_table(weather)

    graph = GraphBuilder().build(schema)

    result = SchemaRetriever().retrieve(
        question=(
            "What percentage was the total unit sales "
            "of store 10 to the total sales of its "
            "weather station?"
        ),
        schema=schema,
        graph=graph,
        max_hops=0,
    )

    assert "sales_in_weather" in result.tables

def test_retrieve_with_diagnostics_exposes_lexical_seeds():
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="customers",
            columns=[
                Column(
                    name="customer_id",
                    data_type="integer",
                ),
                Column(
                    name="name",
                    data_type="text",
                ),
            ],
        )
    )

    schema.add_table(
        Table(
            name="orders",
            columns=[
                Column(
                    name="order_id",
                    data_type="integer",
                ),
                Column(
                    name="customer_id",
                    data_type="integer",
                ),
            ],
        )
    )

    graph = GraphBuilder().build(schema)

    retriever = SchemaRetriever()

    result, diagnostics = retriever.retrieve_with_diagnostics(
        question="Show customer names",
        schema=schema,
        graph=graph,
        max_hops=0,
    )

    assert "customers" in diagnostics["lexical_tables"]
    assert "customers.name" in diagnostics["lexical_columns"]

    assert diagnostics["final_tables"] == sorted(
        result.tables
    )