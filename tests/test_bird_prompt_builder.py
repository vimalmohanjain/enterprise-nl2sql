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