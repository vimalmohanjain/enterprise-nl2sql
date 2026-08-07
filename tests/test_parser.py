from src.schema_graph.parser import SchemaParser


def test_parse_table_name():

    sql = """
    CREATE TABLE employees(
        employee_id INTEGER,
        name TEXT
    );
    """

    parser = SchemaParser()

    schema = parser.parse_sql(sql)
    print(schema.tables)

    assert "employees" in schema.tables