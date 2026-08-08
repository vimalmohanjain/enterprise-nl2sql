import networkx as nx

from src.schema_graph.parser import SchemaParser
from src.schema_graph.graph_builder import GraphBuilder


def test_build_returns_networkx_multidigraph():
    sql = """
    CREATE TABLE departments (
        department_id INT PRIMARY KEY
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    assert isinstance(graph, nx.MultiDiGraph)

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

    assert "employees" in graph.nodes
    assert "departments" in graph.nodes

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

    assert "departments" in graph.nodes 
    assert "employees" in graph.nodes
    assert graph.has_edge("employees", "departments")
    
    edges = graph.get_edge_data("employees", "departments")
    assert len(edges) == 1

    edge = next(iter(edges.values()))

    assert edge["source_columns"] == ["department_id"]
    assert edge["target_columns"] == ["department_id"]  
    
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

    assert "departments" in graph.nodes
    assert "projects" in graph.nodes
    assert "employees" in graph.nodes

    assert graph.has_edge("employees", "departments")
    assert graph.has_edge("employees", "projects")

    assert len(graph.get_edge_data("employees", "departments")) == 1
    assert len(graph.get_edge_data("employees", "projects")) == 1

def test_build_table_without_foreign_keys():
    sql = """
    CREATE TABLE departments (
        department_id INT PRIMARY KEY,
        name TEXT
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    assert set(graph.nodes) == {"departments"}
    assert graph.number_of_edges() == 0

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

    assert set(graph.nodes) == {"departments", "products"}
    assert graph.number_of_edges() == 0


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

    edges = graph.get_edge_data("employees", "departments")
    assert len(edges) == 1

    edge = next(iter(edges.values()))

    assert edge["source_columns"] == ["department_id"]
    assert edge["target_columns"] == ["department_id"]

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

    edges = graph.get_edge_data("shipments", "orders")
    assert len(edges) == 1

    edge = next(iter(edges.values()))
    assert edge["source_columns"] == [
        "order_id",
        "product_id",
    ]

    assert edge["target_columns"] == [
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

    edges = graph.get_edge_data("reviews", "employees")
    assert len(edges) == 2

    edge_data = list(edges.values())

    assert {
        tuple(edge["source_columns"])
        for edge in edge_data
    } == {
        ("manager_id",),
        ("reviewer_id",),
    }

    for edge in edge_data:
        assert edge["target_columns"] == ["employee_id"]