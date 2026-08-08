from src.schema_graph.parser import SchemaParser
from src.schema_graph.graph_builder import GraphBuilder

def test_build_table_nodes():
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

    assert "departments" in graph
    assert "employees" in graph
    assert graph["departments"] == []

def test_build_table_relationships():
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

    assert graph["departments"] == []
    assert len(graph["employees"]) == 1

    relationship = graph["employees"][0]
    assert relationship.target_table == "departments"
    assert relationship.source_columns == ["department_id"]
    assert relationship.target_columns == ["department_id"]

def test_build_multiple_table_relationships():
    sql = """
    CREATE TABLE departments (
        department_id INT PRIMARY KEY
    );

    CREATE TABLE projects (
        project_id INT PRIMARY KEY
    );

    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        department_id INT,
        project_id INT,
        FOREIGN KEY (department_id)
            REFERENCES departments(department_id),
        FOREIGN KEY (project_id)
            REFERENCES projects(project_id)
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    assert graph["departments"] == []
    assert graph["projects"] == []

    relationships = graph["employees"]
    assert len(relationships) == 2
    assert {relationship.target_table for relationship in relationships} == {
        "departments",
        "projects",
    }

def test_build_table_without_foreign_keys():
    sql = """
    CREATE TABLE departments (
        department_id INT PRIMARY KEY,
        name TEXT
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    assert graph == {
        "departments": []
    }

def test_build_disconnected_tables():
    sql = """
    CREATE TABLE departments (
        department_id INT PRIMARY KEY
    );

    CREATE TABLE products (
        product_id INT PRIMARY KEY
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    assert graph == {
        "departments": [],
        "products": [],
    }

def test_build_relationship_with_columns():
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

    relationship = graph["employees"][0]
    assert relationship.source_columns == ["department_id"]
    assert relationship.target_columns == ["department_id"]

def test_build_composite_relationship_with_columns():
    sql = """
    CREATE TABLE orders (
        order_id INT,
        product_id INT,
        PRIMARY KEY(order_id, product_id)
    );

    CREATE TABLE shipments (
        order_id INT,
        product_id INT,
        FOREIGN KEY (order_id, product_id)
            REFERENCES orders(order_id, product_id)
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    relationship = graph["shipments"][0]
    assert relationship.target_table == "orders"
    assert relationship.source_columns == [
        "order_id",
        "product_id",
    ]

    assert relationship.target_columns == [
        "order_id",
        "product_id",
    ]

def test_build_multiple_foreign_keys_to_same_table():
    sql = """
    CREATE TABLE employees (
        employee_id INT PRIMARY KEY
    );

    CREATE TABLE reviews (
        review_id INT PRIMARY KEY,
        manager_id INT,
        reviewer_id INT,

        FOREIGN KEY (manager_id)
            REFERENCES employees(employee_id),

        FOREIGN KEY (reviewer_id)
            REFERENCES employees(employee_id)
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    relationships = graph["reviews"]

    assert len(relationships) == 2

    assert relationships[0].source_columns == ["manager_id"]
    assert relationships[0].target_table == "employees"
    assert relationships[0].target_columns == ["employee_id"]

    assert relationships[1].source_columns == ["reviewer_id"]
    assert relationships[1].target_table == "employees"
    assert relationships[1].target_columns == ["employee_id"]