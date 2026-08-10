from training.plan_sql_parser import PlanSQLParser


def test_parser_extracts_sql_from_plan_response():
    text = (
        "<plan>\n"
        "TABLES: employees\n"
        "</plan>\n"
        "<sql>\n"
        "SELECT name FROM employees\n"
        "</sql>"
    )

    assert PlanSQLParser().parse(text) == (
        "SELECT name FROM employees"
    )


def test_parser_handles_missing_closing_sql_tag():
    text = (
        "<plan>\n"
        "TABLES: employees\n"
        "</plan>\n"
        "<sql>\n"
        "SELECT name FROM employees"
    )

    assert PlanSQLParser().parse(text) == (
        "SELECT name FROM employees"
    )


def test_parser_falls_back_to_raw_sql():
    text = "SELECT name FROM employees"

    assert PlanSQLParser().parse(text) == text