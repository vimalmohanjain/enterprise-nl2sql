from training.sql_plan import SQLPlanBuilder


def test_sql_plan_extracts_structure():
    sql = (
        "SELECT SUM(T2.price) "
        "FROM customer AS T1 "
        "INNER JOIN order_line AS T2 "
        "ON T1.customer_id = T2.customer_id "
        "WHERE T1.name = 'Lucas' "
        "GROUP BY T1.customer_id "
        "ORDER BY SUM(T2.price) DESC "
        "LIMIT 1"
    )

    plan = SQLPlanBuilder().build(sql)

    assert "TABLES: customer; order_line" in plan

    assert (
        "JOINS: T1.customer_id = T2.customer_id"
        in plan
    )

    assert (
        "FILTERS: T1.name = 'Lucas'"
        in plan
    )

    assert (
        "GROUPING: T1.customer_id"
        in plan
    )

    assert (
        "AGGREGATES: SUM(T2.price)"
        in plan
    )

    assert (
        "ORDERING: SUM(T2.price) DESC"
        in plan
    )

    assert "LIMIT: 1" in plan
    assert "SUBQUERIES: 0" in plan