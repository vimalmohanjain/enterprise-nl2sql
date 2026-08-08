from src.schema_graph.evaluator import SQLEvaluator
from src.schema_graph.models import EvaluationExample, EvaluationResult
import pytest


def test_evaluator_exact_match():
    evaluator = SQLEvaluator()

    result = evaluator.evaluate(
        predicted_sql="SELECT * FROM employees",
        expected_sql="SELECT * FROM employees",
    )

    assert result is True


def test_evaluator_ignores_whitespace():
    evaluator = SQLEvaluator()

    result = evaluator.evaluate(
        predicted_sql="""
            SELECT *
            FROM employees
        """,
        expected_sql="SELECT * FROM employees",
    )

    assert result is True


def test_evaluator_detects_different_sql():
    evaluator = SQLEvaluator()

    result = evaluator.evaluate(
        predicted_sql="SELECT name FROM employees",
        expected_sql="SELECT salary FROM employees",
    )

    assert result is False

def test_evaluator_ignores_sql_case():
    evaluator = SQLEvaluator()

    result = evaluator.evaluate(
        predicted_sql="select * from employees",
        expected_sql="SELECT * FROM employees",
    )

    assert result is True


def test_evaluator_ignores_trailing_semicolon():
    evaluator = SQLEvaluator()

    result = evaluator.evaluate(
        predicted_sql="SELECT * FROM employees;",
        expected_sql="SELECT * FROM employees",
    )

    assert result is True


def test_evaluator_ignores_case_whitespace_and_semicolon():
    evaluator = SQLEvaluator()

    result = evaluator.evaluate(
        predicted_sql="""
            select name
            from employees;
        """,
        expected_sql="SELECT name FROM employees",
    )

    assert result is True

def test_evaluator_batch_accuracy():
    evaluator = SQLEvaluator()

    examples = [
        EvaluationExample(
            question="Show all employees",
            expected_sql="SELECT * FROM employees",
        ),
        EvaluationExample(
            question="Show employee names",
            expected_sql="SELECT name FROM employees",
        ),
    ]

    predictions = [
        "SELECT * FROM employees",
        "SELECT salary FROM employees",
    ]

    result = evaluator.evaluate_batch(
        examples=examples,
        predictions=predictions,
    )

    assert result.total == 2
    assert result.correct == 1
    assert result.accuracy == 0.5


def test_evaluator_batch_all_correct():
    evaluator = SQLEvaluator()

    examples = [
        EvaluationExample(
            question="Show all employees",
            expected_sql="SELECT * FROM employees",
        ),
        EvaluationExample(
            question="Show employee names",
            expected_sql="SELECT name FROM employees",
        ),
    ]

    predictions = [
        "select * from employees;",
        "SELECT name FROM employees",
    ]

    result = evaluator.evaluate_batch(
        examples=examples,
        predictions=predictions,
    )

    assert result.total == 2
    assert result.correct == 2
    assert result.accuracy == 1.0

def test_evaluator_rejects_mismatched_batch_lengths():
    evaluator = SQLEvaluator()

    examples = [
        EvaluationExample(
            question="Show all employees",
            expected_sql="SELECT * FROM employees",
        )
    ]

    predictions = [
        "SELECT * FROM employees",
        "SELECT name FROM employees",
    ]

    with pytest.raises(
        ValueError,
        match="Examples and predictions must have the same length",
    ):
        evaluator.evaluate_batch(
            examples=examples,
            predictions=predictions,
        )

import sqlite3


def create_test_database():
    connection = sqlite3.connect(":memory:")

    connection.executescript(
        """
        CREATE TABLE departments (
            department_id INTEGER PRIMARY KEY,
            name TEXT
        );

        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY,
            name TEXT,
            salary REAL,
            department_id INTEGER
        );

        INSERT INTO departments VALUES
            (1, 'Engineering'),
            (2, 'Sales');

        INSERT INTO employees VALUES
            (1, 'Alice', 70000, 1),
            (2, 'Bob', 60000, 1),
            (3, 'Charlie', 45000, 2);
        """
    )

    return connection


def test_execution_evaluator_accepts_alias_difference():
    evaluator = SQLEvaluator()
    connection = create_test_database()

    result = evaluator.evaluate_execution(
        predicted_sql=(
            "SELECT AVG(salary) AS average_salary "
            "FROM employees"
        ),
        expected_sql=(
            "SELECT AVG(salary) "
            "FROM employees"
        ),
        connection=connection,
    )

    assert result is True


def test_execution_evaluator_detects_different_results():
    evaluator = SQLEvaluator()
    connection = create_test_database()

    result = evaluator.evaluate_execution(
        predicted_sql="SELECT name FROM employees",
        expected_sql="SELECT salary FROM employees",
        connection=connection,
    )

    assert result is False

def test_evaluator_batch_execution_accuracy():
    evaluator = SQLEvaluator()
    connection = create_test_database()

    examples = [
        EvaluationExample(
            question="Average salary",
            expected_sql="SELECT AVG(salary) FROM employees",
        ),
        EvaluationExample(
            question="Employee names",
            expected_sql="SELECT name FROM employees",
        ),
    ]

    predictions = [
        # Different syntax/alias, same result
        "SELECT AVG(salary) AS average_salary FROM employees",

        # Wrong result
        "SELECT salary FROM employees",
    ]

    result = evaluator.evaluate_execution_batch(
        examples=examples,
        predictions=predictions,
        connection=connection,
    )

    assert result.total == 2
    assert result.correct == 1
    assert result.accuracy == 0.5

def test_execution_evaluator_handles_invalid_sql():
    evaluator = SQLEvaluator()
    connection = create_test_database()

    result = evaluator.evaluate_execution(
        predicted_sql="THIS IS NOT SQL",
        expected_sql="SELECT name FROM employees",
        connection=connection,
    )

    assert result is False

def test_evaluator_creates_detailed_report():
    evaluator = SQLEvaluator()
    connection = create_test_database()

    examples = [
        EvaluationExample(
            question="Average salary",
            expected_sql="SELECT AVG(salary) FROM employees",
        ),
        EvaluationExample(
            question="Employee names",
            expected_sql="SELECT name FROM employees",
        ),
    ]

    predictions = [
        "SELECT AVG(salary) AS average_salary FROM employees",
        "SELECT salary FROM employees",
    ]

    details = evaluator.evaluate_details(
        examples=examples,
        predictions=predictions,
        connection=connection,
    )

    assert len(details) == 2

    assert details[0].question == "Average salary"
    assert details[0].strict_match is False
    assert details[0].execution_match is True

    assert details[1].question == "Employee names"
    assert details[1].strict_match is False
    assert details[1].execution_match is False