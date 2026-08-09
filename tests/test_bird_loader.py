import json

from src.schema_graph.bird_loader import BirdDatasetLoader
from src.schema_graph.models import DatabaseSchema


def test_bird_loader_loads_training_examples(tmp_path):
    train_file = tmp_path / "train.json"

    train_file.write_text(
        json.dumps(
            [
                {
                    "db_id": "company",
                    "question": "Show employee names",
                    "evidence": "",
                    "SQL": "SELECT name FROM employees",
                }
            ]
        ),
        encoding="utf-8",
    )

    loader = BirdDatasetLoader()

    examples = loader.load_examples(train_file)

    assert len(examples) == 1

    example = examples[0]

    assert example.question == "Show employee names"
    assert example.sql == "SELECT name FROM employees"

def test_bird_loader_loads_schema_by_database_id(tmp_path):
    tables_file = tmp_path / "train_tables.json"

    tables_file.write_text(
        json.dumps(
            [
                {
                    "db_id": "company",
                    "table_names_original": [
                        "departments",
                        "employees",
                    ],
                    "column_names_original": [
                        [-1, "*"],
                        [0, "department_id"],
                        [0, "name"],
                        [1, "employee_id"],
                        [1, "name"],
                        [1, "department_id"],
                        [1, "salary"],
                    ],
                    "column_types": [
                        "text",
                        "integer",
                        "text",
                        "integer",
                        "text",
                        "integer",
                        "integer",
                    ],
                    "primary_keys": [1, 3],
                    "foreign_keys": [
                        [5, 1],
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    loader = BirdDatasetLoader()

    schema = loader.load_schema(
        tables_file,
        db_id="company",
    )

    assert schema["db_id"] == "company"

    assert schema["table_names_original"] == [
        "departments",
        "employees",
    ]

    assert schema["foreign_keys"] == [
        [5, 1],
    ]

def test_bird_loader_converts_schema_to_domain_model():
    bird_schema = {
        "db_id": "company",
        "table_names_original": [
            "departments",
            "employees",
        ],
        "column_names_original": [
            [-1, "*"],
            [0, "department_id"],
            [0, "name"],
            [1, "employee_id"],
            [1, "name"],
            [1, "department_id"],
            [1, "salary"],
        ],
        "column_types": [
            "text",
            "integer",
            "text",
            "integer",
            "text",
            "integer",
            "integer",
        ],
        "primary_keys": [1, 3],
        "foreign_keys": [
            [5, 1],
        ],
    }

    loader = BirdDatasetLoader()

    schema = loader.convert_schema(bird_schema)

    assert isinstance(schema, DatabaseSchema)

    departments = schema.get_table("departments")
    employees = schema.get_table("employees")

    assert departments is not None
    assert employees is not None

    assert departments.get_column("department_id").is_primary_key is True
    assert employees.get_column("employee_id").is_primary_key is True

    department_fk_column = employees.get_column("department_id")

    assert department_fk_column.is_foreign_key is True

    assert len(employees.foreign_keys) == 1

    foreign_key = employees.foreign_keys[0]

    assert foreign_key.source_columns == ["department_id"]
    assert foreign_key.target_table == "departments"
    assert foreign_key.target_columns == ["department_id"]

def test_bird_loader_handles_composite_primary_keys():
    bird_schema = {
        "db_id": "sales",
        "table_names_original": [
            "order_items",
        ],
        "column_names_original": [
            [-1, "*"],
            [0, "order_id"],
            [0, "product_id"],
            [0, "quantity"],
        ],
        "column_types": [
            "text",
            "integer",
            "integer",
            "integer",
        ],
        "primary_keys": [
            [1, 2],
        ],
        "foreign_keys": [],
    }

    loader = BirdDatasetLoader()

    schema = loader.convert_schema(bird_schema)

    table = schema.get_table("order_items")

    assert table is not None

    assert table.get_column("order_id").is_primary_key is True
    assert table.get_column("product_id").is_primary_key is True
    assert table.get_column("quantity").is_primary_key is False