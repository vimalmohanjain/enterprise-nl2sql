from src.schema_graph.parser import SchemaParser
from src.schema_graph.graph_builder import GraphBuilder
from src.schema_graph.retriever import SchemaRetriever
from src.schema_graph.context_builder import ContextBuilder
from src.schema_graph.prompt_builder import PromptBuilder
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

def test_prompt_output_is_deterministic():
    context = create_context()

    builder = PromptBuilder()

    prompt1 = builder.build(
        question="Show employee salary by department",
        context=context,
    )

    prompt2 = builder.build(
        question="Show employee salary by department",
        context=context,
    )

    assert prompt1 == prompt2


def test_prompt_contains_composite_relationship():
    context = SchemaContext(
        tables={},
        relationships=[
            Relationship(
                source_table="shipments",
                target_table="orders",
                source_columns=["order_id", "product_id"],
                target_columns=["order_id", "product_id"],
            )
        ],
    )

    prompt = PromptBuilder().build(
        question="Show shipment order information",
        context=context,
    )

    assert (
        "shipments.order_id -> orders.order_id"
        in prompt
    )

    assert (
        "shipments.product_id -> orders.product_id"
        in prompt
    )


def test_prompt_handles_empty_context():
    context = SchemaContext()

    prompt = PromptBuilder().build(
        question="Show all employees",
        context=context,
    )

    assert "Show all employees" in prompt
    assert "Generate SQL only." in prompt

def test_retrieval_context_prompt_pipeline():
    sql = """
    CREATE TABLE departments (
        department_id INT PRIMARY KEY,
        name TEXT
    );

    CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        salary REAL,
        department_id INT,
        FOREIGN KEY (department_id)
            REFERENCES departments(department_id)
    );
    """

    schema = SchemaParser().parse(sql)
    graph = GraphBuilder().build(schema)

    result = SchemaRetriever().retrieve(
        "Show employee salary by department",
        schema,
        graph,
    )

    context = ContextBuilder().build(
        result,
        schema,
    )

    prompt = PromptBuilder().build(
        question="Show employee salary by department",
        context=context,
    )

    assert "Table: employees" in prompt
    assert "salary" in prompt

    assert "Table: departments" in prompt
    assert "department_id" in prompt

    assert (
        "employees.department_id -> departments.department_id"
        in prompt
    )

    assert "Show employee salary by department" in prompt
    assert "Generate SQL only." in prompt

def test_prompt_builder_formats_schema_context_only():
    context = create_context()

    builder = PromptBuilder()

    schema_text = builder.build_schema_context(context)

    assert "Table: employees" in schema_text
    assert "salary" in schema_text
    assert "Table: departments" in schema_text
    assert (
        "employees.department_id -> departments.department_id"
        in schema_text
    )

    assert "Question:" not in schema_text
    assert "Generate SQL only." not in schema_text