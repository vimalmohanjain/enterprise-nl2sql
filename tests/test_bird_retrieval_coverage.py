from src.schema_graph.graph_builder import GraphBuilder
from src.schema_graph.models import (
    Column,
    DatabaseSchema,
    ForeignKey,
    Table,
)
from src.schema_graph.retriever import SchemaRetriever


def test_retriever_includes_tables_required_by_question():
    schema = DatabaseSchema()

    departments = Table(
        name="departments",
        columns=[
            Column(
                name="department_id",
                data_type="integer",
                is_primary_key=True,
            ),
            Column(
                name="name",
                data_type="text",
            ),
        ],
    )

    employees = Table(
        name="employees",
        columns=[
            Column(
                name="employee_id",
                data_type="integer",
                is_primary_key=True,
            ),
            Column(
                name="name",
                data_type="text",
            ),
            Column(
                name="department_id",
                data_type="integer",
                is_foreign_key=True,
            ),
        ],
        foreign_keys=[
            ForeignKey(
                source_columns=["department_id"],
                target_table="departments",
                target_columns=["department_id"],
            )
        ],
    )

    schema.add_table(departments)
    schema.add_table(employees)

    graph = GraphBuilder().build(schema)

    retriever = SchemaRetriever()

    result = retriever.retrieve(
        question="Show employee names and their department names",
        schema=schema,
        graph=graph,
        max_hops=1,
    )

    assert "employees" in result.tables
    assert "departments" in result.tables