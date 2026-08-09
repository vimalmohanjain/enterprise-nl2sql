import json

from training.jsonl import export_records_jsonl


def test_export_records_jsonl(tmp_path):
    records = [
        {
            "instruction": "Show employee names",
            "schema_context": "Table: employees",
            "output": "SELECT name FROM employees",
            "text": (
                "Table: employees\n"
                "Show employee names\n"
                "SELECT name FROM employees"
            ),
        }
    ]

    output_file = tmp_path / "training.jsonl"

    export_records_jsonl(
        records,
        output_file,
    )

    lines = output_file.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    saved = json.loads(lines[0])

    assert saved == records[0]