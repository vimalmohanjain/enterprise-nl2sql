import json
from pathlib import Path

from .models import DatabaseSchema, DatasetExample, Table

class DatasetGenerator:
    """Generate natural-language-to-SQL training examples."""
    def export_jsonl(
        self,
        examples: list[DatasetExample],
        path: str | Path,
    ) -> None:
        output_path = Path(path)

        with output_path.open("w", encoding="utf-8") as file:
            for example in examples:
                record = {
                    "question": example.question,
                    "sql": example.sql,
                }

                file.write(json.dumps(record) + "\n")

# generate()
# ├── _generate_select_examples()
# ├── _generate_filter_examples()
# ├── _generate_aggregate_examples()
# └── _generate_join_examples()

# DatasetExample model
# ✅ DatasetGenerator
# ✅ SELECT *
# ✅ Single-column SELECT
# ✅ Multi-column SELECT
# ✅ Numeric WHERE
# ✅ Foreign-key JOIN
# ✅ COUNT(*)
# ✅ AVG()
# ⬜ Exclude PK/FK columns from inappropriate aggregates
# ⬜ SUM, MIN, MAX
# ⬜ GROUP BY
# ⬜ ORDER BY / LIMIT
# ⬜ JOIN + filter examples
# ⬜ Better/natural question variations
# ⬜ Dataset serialization/export, probably JSONL
# ⬜ Tests for generation edge cases

    
    def generate(self, schema: DatabaseSchema) -> list[DatasetExample]:
        examples = []

        for table in schema:
            examples.extend(self._generate_select_examples(table))
            examples.extend(self._generate_filter_examples(table))
            examples.extend(self._generate_aggregate_examples(table))
            examples.extend(self._generate_group_by_examples(table))
            examples.extend(self._generate_order_by_examples(table))

        examples.extend(self._generate_join_examples(schema))
        examples.extend(self._generate_join_filter_examples(schema))

        return examples

    def _generate_select_examples(
        self,
        table: Table,
    ) -> list[DatasetExample]:
        examples = []

        # Example 1: select all rows
        examples.append(
            DatasetExample(
                question=f"Show all {table.name}",
                sql=f"SELECT * FROM {table.name}",
            )
        )

        # Example 2: select each column
        for column in table.columns:
            examples.append(
                DatasetExample(
                    question=f"Show {column.name} from {table.name}",
                    sql=f"SELECT {column.name} FROM {table.name}",
                )
            )

        # Example 3: select adjacent pairs of columns
        for index in range(len(table.columns) - 1):
            first_column = table.columns[index]
            second_column = table.columns[index + 1]

            examples.append(
                DatasetExample(
                    question=(
                        f"Show {first_column.name} "
                        f"and {second_column.name} "
                        f"from {table.name}"
                    ),
                    sql=(
                        f"SELECT {first_column.name}, "
                        f"{second_column.name} "
                        f"FROM {table.name}"
                    ),
                )
            )

        return examples

    def _generate_filter_examples(
        self,
        table: Table,
    ) -> list[DatasetExample]:
        examples = []

        for column in table.columns:
            if column.data_type.upper() in {
                "INT",
                "INTEGER",
                "REAL",
                "FLOAT",
                "DOUBLE",
            }:
                examples.append(
                    DatasetExample(
                        question=(
                            f"Show {table.name} "
                            f"where {column.name} "
                            f"is greater than 50000"
                        ),
                        sql=(
                            f"SELECT * FROM {table.name} "
                            f"WHERE {column.name} > 50000"
                        ),
                    )
                )

        return examples

    def _generate_join_examples(
        self,
        schema: DatabaseSchema,
    ) -> list[DatasetExample]:
        examples = []

        for table in schema:
            for foreign_key in table.foreign_keys:
                source_table = table.name
                target_table = foreign_key.target_table

                source_columns = foreign_key.source_columns
                target_columns = foreign_key.target_columns

                source_table_model = schema.get_table(source_table)
                target_table_model = schema.get_table(target_table)

                if source_table_model is None or target_table_model is None:
                    continue

                source_column = next(
                    (
                        column
                        for column in source_table_model.columns
                        if (
                            column.name not in source_columns
                            and not column.is_primary_key
                        )
                    ),
                    None,
                )

                target_column = next(
                    (
                        column
                        for column in target_table_model.columns
                        if (
                            column.name not in target_columns
                            and not column.is_primary_key
                        )
                    ),
                    None,
                )

                if source_column is None or target_column is None:
                    continue

                join_conditions = " AND ".join(
                    f"{source_table}.{source_name} = "
                    f"{target_table}.{target_name}"
                    for source_name, target_name in zip(
                        source_columns,
                        target_columns,
                    )
                )

                examples.append(
                    DatasetExample(
                        question=(
                            f"Show {source_table} and "
                            f"{target_table} information"
                        ),
                        sql=(
                            f"SELECT {source_table}.{source_column.name}, "
                            f"{target_table}.{target_column.name} "
                            f"FROM {source_table} "
                            f"JOIN {target_table} "
                            f"ON {join_conditions}"
                        ),
                    )
                )

        return examples

    def _generate_aggregate_examples(
        self,
        table: Table,
    ) -> list[DatasetExample]:
        examples = [
            DatasetExample(
                question=f"How many {table.name} are there?",
                sql=f"SELECT COUNT(*) FROM {table.name}",
            )
        ]

        numeric_types = {
            "INT",
            "INTEGER",
            "REAL",
            "FLOAT",
            "DOUBLE",
        }

        for column in table.columns:
            if (
                column.data_type.upper() in numeric_types
                and not column.is_primary_key
                and not column.is_foreign_key
            ):
                aggregate_templates = [
                    ("average", "AVG"),
                    ("total", "SUM"),
                    ("minimum", "MIN"),
                    ("maximum", "MAX"),
                ]

                for label, function in aggregate_templates:
                    examples.append(
                        DatasetExample(
                            question=(
                                f"What is the {label} {column.name} "
                                f"of {table.name}?"
                            ),
                            sql=(
                                f"SELECT {function}({column.name}) "
                                f"FROM {table.name}"
                            ),
                        )
                    )

        return examples

    def _generate_group_by_examples(
        self,
        table: Table,
    ) -> list[DatasetExample]:
        examples = []

        numeric_types = {
            "INT",
            "INTEGER",
            "REAL",
            "FLOAT",
            "DOUBLE",
        }

        # Columns that make sense as measures: salary, amount, price, etc.
        measure_columns = [
            column
            for column in table.columns
            if (
                column.data_type.upper() in numeric_types
                and not column.is_primary_key
                and not column.is_foreign_key
                and not column.name.endswith("_id")
            )
        ]

        # Columns that make sense for grouping.
        group_columns = [
            column
            for column in table.columns
            if (
                column.is_foreign_key
                or column.name.endswith("_id")
                or column.data_type.upper() not in numeric_types
            )
            and not column.is_primary_key
        ]

        for group_column in group_columns:
            for measure_column in measure_columns:
                examples.append(
                    DatasetExample(
                        question=(
                            f"What is the average {measure_column.name} "
                            f"by {group_column.name} in {table.name}?"
                        ),
                        sql=(
                            f"SELECT {group_column.name}, "
                            f"AVG({measure_column.name}) "
                            f"FROM {table.name} "
                            f"GROUP BY {group_column.name}"
                        ),
                    )
                )

        return examples


    def _generate_order_by_examples(
        self,
        table: Table,
    ) -> list[DatasetExample]:
        examples = []

        numeric_types = {
            "INT",
            "INTEGER",
            "REAL",
            "FLOAT",
            "DOUBLE",
        }

        for column in table.columns:
            if (
                column.data_type.upper() in numeric_types
                and not column.is_primary_key
                and not column.is_foreign_key
            ):
                examples.append(
                    DatasetExample(
                        question=(
                            f"Show top 10 {table.name} "
                            f"by {column.name}"
                        ),
                        sql=(
                            f"SELECT * FROM {table.name} "
                            f"ORDER BY {column.name} DESC LIMIT 10"
                        ),
                    )
                )

        return examples

    def _generate_join_filter_examples(
        self,
        schema: DatabaseSchema,
    ) -> list[DatasetExample]:
        examples = []

        numeric_types = {
            "INT",
            "INTEGER",
            "REAL",
            "FLOAT",
            "DOUBLE",
        }

        for table in schema:
            for foreign_key in table.foreign_keys:
                source_table = table.name
                target_table = foreign_key.target_table

                source_model = schema.get_table(source_table)
                target_model = schema.get_table(target_table)

                if source_model is None or target_model is None:
                    continue

                source_column = next(
                    (
                        column
                        for column in source_model.columns
                        if (
                            column.name not in foreign_key.source_columns
                            and not column.is_primary_key
                        )
                    ),
                    None,
                )

                target_column = next(
                    (
                        column
                        for column in target_model.columns
                        if (
                            column.name not in foreign_key.target_columns
                            and not column.is_primary_key
                        )
                    ),
                    None,
                )

                filter_column = next(
                    (
                        column
                        for column in source_model.columns
                        if (
                            column.data_type.upper() in numeric_types
                            and not column.is_primary_key
                            and not column.is_foreign_key
                            and column.name not in foreign_key.source_columns
                        )
                    ),
                    None,
                )

                if (
                    source_column is None
                    or target_column is None
                    or filter_column is None
                ):
                    continue

                join_conditions = " AND ".join(
                    f"{source_table}.{source_name} = "
                    f"{target_table}.{target_name}"
                    for source_name, target_name in zip(
                        foreign_key.source_columns,
                        foreign_key.target_columns,
                    )
                )

                examples.append(
                    DatasetExample(
                        question=(
                            f"Show {source_table} and {target_table} "
                            f"where {filter_column.name} "
                            f"is greater than 50000"
                        ),
                        sql=(
                            f"SELECT {source_table}.{source_column.name}, "
                            f"{target_table}.{target_column.name} "
                            f"FROM {source_table} "
                            f"JOIN {target_table} "
                            f"ON {join_conditions} "
                            f"WHERE {source_table}.{filter_column.name} > 50000"
                        ),
                    )
                )

        return examples