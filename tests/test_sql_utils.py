from src.schema_graph.sql_utils import clean_sql


def test_clean_sql_returns_plain_sql():
    assert clean_sql(
        "SELECT name FROM employees;"
    ) == "SELECT name FROM employees;"


def test_clean_sql_extracts_fenced_sql():
    response = """
    ```sql
    SELECT name FROM employees;
    ```
    """

    assert clean_sql(response) == (
        "SELECT name FROM employees;"
    )


def test_clean_sql_rejects_empty_response():
    try:
        clean_sql("   ")
        assert False
    except ValueError:
        pass