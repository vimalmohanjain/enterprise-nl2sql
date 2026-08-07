from src.schema_graph.graph_builder import GraphBuilder
from src.schema_graph.parser import SchemaParser


def test_parse_table_name():
    sql = """
    CREATE TABLE departments (
    department_id INT PRIMARY KEY,
    name TEXT
    );

    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        department_id INT,
        FOREIGN KEY (department_id)
            REFERENCES departments(department_id)
    );
    """

    parser = SchemaParser()
    schema = parser.parse(sql)
    assert "employees" in schema.tables


def test_extract_columns():
    sql = """
    CREATE TABLE employees(
        employee_id INT PRIMARY KEY,
        name TEXT,
        salary REAL
    );
    """

    parser = SchemaParser()
    schema = parser.parse(sql)
    employee_table = schema.get_table("employees")

    assert employee_table is not None
    assert len(employee_table.columns) == 3

    assert employee_table.columns[0].is_primary_key
    assert employee_table.columns[0].name == "employee_id"
    assert employee_table.columns[0].data_type == "INT"

    assert not employee_table.columns[1].is_primary_key
    assert employee_table.columns[1].name == "name"
    assert employee_table.columns[1].data_type == "TEXT"

    assert employee_table.columns[2].name == "salary"
    assert employee_table.columns[2].data_type == "FLOAT"

    assert len(schema.tables) == 1
    assert len(schema.get_table("employees").columns) == 3


def test_table_level_primary_key():
    sql = """
    CREATE TABLE employees(
        employee_id INT,
        name TEXT,
        PRIMARY KEY(employee_id)
    );
    """

    parser = SchemaParser()
    schema = parser.parse(sql)
    employee_table = schema.get_table("employees")
    assert employee_table is not None
    assert employee_table.get_column("employee_id").is_primary_key
    assert not employee_table.get_column("name").is_primary_key


def test_parse_simple_foreign_key():
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
    parser = SchemaParser()
    schema = parser.parse(sql)
    employee_table = schema.get_table("employees")
    assert employee_table is not None
    assert len(employee_table.foreign_keys) == 1
    foreign_key = employee_table.foreign_keys[0]
    assert foreign_key.source_columns == ["department_id"]
    assert foreign_key.target_table == "departments"
    assert foreign_key.target_columns == ["department_id"]


def test_parse_composite_foreign_key():
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
    parser = SchemaParser()
    schema = parser.parse(sql)
    shipment_table = schema.get_table("shipments")
    assert shipment_table is not None
    foreign_keys = shipment_table.foreign_keys
    assert len(foreign_keys) == 1
    assert foreign_keys[0].source_columns == ["order_id", "product_id"]
    assert foreign_keys[0].target_table == "orders"
    assert foreign_keys[0].target_columns == ["order_id", "product_id"]
