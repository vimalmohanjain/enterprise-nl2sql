from scripts.run_bird_adapter_evaluation import summarize_results
from src.schema_graph.models import EvaluationDetail


def test_summarize_results():
    results = [
        EvaluationDetail(
            question="Q1",
            expected_sql="SELECT 1",
            predicted_sql="SELECT 1",
            strict_match=True,
            execution_match=True,
        ),
        EvaluationDetail(
            question="Q2",
            expected_sql="SELECT 2",
            predicted_sql="SELECT 3",
            strict_match=False,
            execution_match=False,
        ),
        EvaluationDetail(
            question="Q3",
            expected_sql="SELECT 4",
            predicted_sql="SELECT 5",
            strict_match=False,
            execution_match=True,
        ),
    ]

    summary = summarize_results(results)

    assert summary["total"] == 3
    assert summary["strict_correct"] == 1
    assert summary["execution_correct"] == 2
    assert summary["strict_accuracy"] == 1 / 3
    assert summary["execution_accuracy"] == 2 / 3

from scripts.run_bird_adapter_evaluation import run_evaluation


class FakePipeline:
    def evaluate(self, examples, *, prompt_builder):
        return [
            EvaluationDetail(
                question="Q1",
                expected_sql="SELECT 1",
                predicted_sql="SELECT 1",
                strict_match=True,
                execution_match=True,
            )
        ]


def test_run_evaluation_returns_results_and_summary():
    examples = ["example"]

    results, summary = run_evaluation(
        pipeline=FakePipeline(),
        examples=examples,
        prompt_builder=lambda example: "prompt",
    )

    assert len(results) == 1
    assert summary["total"] == 1
    assert summary["strict_accuracy"] == 1.0
    assert summary["execution_accuracy"] == 1.0

import json

from scripts.run_bird_adapter_evaluation import load_validation_examples


def test_load_validation_examples_reconstructs_bird_split(tmp_path):
    train_file = tmp_path / "train.json"
    tables_file = tmp_path / "train_tables.json"

    train_file.write_text(
        json.dumps(
            [
                {
                    "db_id": f"db_{index}",
                    "question": f"Question {index}",
                    "evidence": "",
                    "SQL": f"SELECT {index}",
                }
                for index in range(10)
            ]
        ),
        encoding="utf-8",
    )

    tables_file.write_text(
        json.dumps(
            [
                {
                    "db_id": f"db_{index}",
                    "table_names_original": ["items"],
                    "column_names_original": [
                        [-1, "*"],
                        [0, "id"],
                    ],
                    "column_types": [
                        "text",
                        "integer",
                    ],
                    "primary_keys": [1],
                    "foreign_keys": [],
                }
                for index in range(10)
            ]
        ),
        encoding="utf-8",
    )

    validation = load_validation_examples(
        train_file=train_file,
        tables_file=tables_file,
        validation_ratio=0.2,
        seed=42,
    )

    assert len(validation) == 2
    assert all(example.db_id.startswith("db_") for example in validation)
    assert all(example.expected_sql.startswith("SELECT") for example in validation)