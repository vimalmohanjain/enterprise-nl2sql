from src.schema_graph.models import (
    Column,
    Relationship,
    SchemaContext,
    TableContext,
)
from src.schema_graph.prompt_builder import PromptBuilder


def create_context() -> SchemaContext:
    return SchemaContext(
        tables={
            "employees": TableContext(
                name="employees",
                columns={
                    "employee_id": Column(
                        name="employee_id",
                        data_type="INT",
                        is_primary_key=True,
                    ),
                    "salary": Column(
                        name="salary",
                        data_type="REAL",
                    ),
                    "department_id": Column(
                        name="department_id",
                        data_type="INT",
                    ),
                },
            ),
            "departments": TableContext(
                name="departments",
                columns={
                    "department_id": Column(
                        name="department_id",
                        data_type="INT",
                        is_primary_key=True,
                    ),
                    "name": Column(
                        name="name",
                        data_type="TEXT",
                    ),
                },
            ),
        },
        relationships=[
            Relationship(
                source_table="employees",
                target_table="departments",
                source_columns=["department_id"],
                target_columns=["department_id"],
            )
        ],
    )


def test_prompt_contains_question():
    context = create_context()

    prompt = PromptBuilder().build(
        question="Show employee salary by department",
        context=context,
    )

    assert "Show employee salary by department" in prompt


def test_prompt_contains_tables_and_columns():
    context = create_context()

    prompt = PromptBuilder().build(
        question="Show employee salary by department",
        context=context,
    )

    assert "employees" in prompt
    assert "employee_id" in prompt
    assert "salary" in prompt
    assert "departments" in prompt
    assert "department_id" in prompt
    assert "name" in prompt


def test_prompt_contains_relationship():
    context = create_context()

    prompt = PromptBuilder().build(
        question="Show employee salary by department",
        context=context,
    )

    assert (
        "employees.department_id -> departments.department_id"
        in prompt
    )


def test_prompt_requests_sql_only():
    context = create_context()

    prompt = PromptBuilder().build(
        question="Show employee salary by department",
        context=context,
    )

    assert "SQL only" in prompt