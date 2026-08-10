import json

from training.bird_evaluation import BirdEvaluationExample
from training.bird_prompt_builder import BirdPromptBuilder


def test_bird_prompt_builder_builds_schema_aware_prompt(tmp_path):
    tables_file = tmp_path / "train_tables.json"

    tables_file.write_text(
        json.dumps(
            [
                {
                    "db_id": "company",
                    "table_names_original": ["employees"],
                    "column_names_original": [
                        [-1, "*"],
                        [0, "employee_id"],
                        [0, "name"],
                    ],
                    "column_types": [
                        "text",
                        "integer",
                        "text",
                    ],
                    "primary_keys": [1],
                    "foreign_keys": [],
                }
            ]
        ),
        encoding="utf-8",
    )

    example = BirdEvaluationExample(
        db_id="company",
        question="Show employee names",
        expected_sql="SELECT name FROM employees",
    )

    builder = BirdPromptBuilder(
        tables_file=tables_file,
    )

    prompt = builder.build(example)

    assert "Table: employees" in prompt
    assert "employee_id" in prompt
    assert "Show employee names" in prompt
    assert "Generate SQL only." in prompt

def test_bird_prompt_builder_can_use_retrieved_schema(tmp_path):
    tables_file = tmp_path / "train_tables.json"

    tables_file.write_text(
        json.dumps(
            [
                {
                    "db_id": "company",
                    "table_names_original": [
                        "customers",
                        "transactions",
                        "line_items",
                        "unrelated",
                    ],
                    "column_names_original": [
                        [-1, "*"],
                        [0, "customer_id"],
                        [0, "name"],
                        [1, "transaction_id"],
                        [1, "customer_id"],
                        [2, "transaction_id"],
                        [2, "quantity"],
                        [3, "id"],
                    ],
                    "column_types": [
                        "text",
                        "integer",
                        "text",
                        "integer",
                        "integer",
                        "integer",
                        "integer",
                        "integer",
                    ],
                    "primary_keys": [
                        1,
                        3,
                    ],
                    "foreign_keys": [
                        [4, 1],
                        [5, 3],
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    example = BirdEvaluationExample(
        db_id="company",
        question="Show customers and line_items quantity",
        expected_sql=(
            "SELECT customers.name, line_items.quantity "
            "FROM customers "
            "JOIN transactions "
            "ON transactions.customer_id = customers.customer_id "
            "JOIN line_items "
            "ON line_items.transaction_id = transactions.transaction_id"
        ),
    )

    class FakeRetriever:
        def retrieve(
            self,
            question,
            schema,
            graph,
        ):
            from src.schema_graph.models import (
                Relationship,
                RetrievalResult,
            )

            return RetrievalResult(
                tables={
                    "customers",
                    "transactions",
                    "line_items",
                },
                columns=set(),
                relationships=[
                    Relationship(
                        source_table="transactions",
                        target_table="customers",
                        source_columns=["customer_id"],
                        target_columns=["customer_id"],
                    ),
                    Relationship(
                        source_table="line_items",
                        target_table="transactions",
                        source_columns=["transaction_id"],
                        target_columns=["transaction_id"],
                    ),
                ],
            )

    builder = BirdPromptBuilder(
        tables_file=tables_file,
        retriever=FakeRetriever(),
    )

    prompt = builder.build(example)

    assert "Table: customers" in prompt
    assert "Table: transactions" in prompt
    assert "Table: line_items" in prompt

    assert "Table: unrelated" not in prompt

    assert (
        "transactions.customer_id -> customers.customer_id"
        in prompt
    )

    assert (
        "line_items.transaction_id -> transactions.transaction_id"
        in prompt
    )