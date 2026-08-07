from rich import table

from src.schema_graph.parser import SchemaParser


def test_parse_table_name():

    sql = """
    CREATE TABLE employees(
        employee_id INTEGER,
        name TEXT
    );
    """

    parser = SchemaParser()

    schema = parser.parse(sql)
    print(schema.tables)

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

    table = schema.get_table("employees")

    assert table is not None
    assert len(table.columns) == 3

    assert table.columns[0].is_primary_key
    assert table.columns[0].name == "employee_id"
    assert table.columns[0].data_type == "INT"

    assert not table.columns[1].is_primary_key
    assert table.columns[1].name == "name"
    assert table.columns[1].data_type == "TEXT"

    assert table.columns[2].name == "salary"
    assert table.columns[2].data_type == "FLOAT"

    assert len(schema.tables) == 1
    # assert len(schema.get_table("departments").columns) == 2
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

    table = schema.get_table("employees")

    assert table is not None
    assert table.get_column("employee_id").is_primary_key
    assert not table.get_column("name").is_primary_key