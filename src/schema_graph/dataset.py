import json
from pathlib import Path

from .models import DatabaseSchema, DatasetExample, Table


class DatasetGenerator:
    """Generate natural-language-to-SQL training examples."""

    NUMERIC_TYPES = {
        "INT",
        "INTEGER",
        "REAL",
        "FLOAT",
        "DOUBLE",
    }

    AGGREGATE_TEMPLATES = (
        ("average", "AVG"),
        ("total", "SUM"),
        ("minimum", "MIN"),
        ("maximum", "MAX"),
    )

    def generate(
        self,
        schema: DatabaseSchema,
    ) -> list[DatasetExample]:
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

    def _generate_select_examples(
        self,
        table: Table,
    ) -> list[DatasetExample]:
        examples = [
            DatasetExample(
                question=f"Show all {table.name}",
                sql=f"SELECT * FROM {table.name}",
            )
        ]

        for column in table.columns:
            examples.append(
                DatasetExample(
                    question=f"Show {column.name} from {table.name}",
                    sql=f"SELECT {column.name} FROM {table.name}",
                )
            )

        for index in range(len(table.columns) - 1):
            first = table.columns[index]
            second = table.columns[index + 1]

            examples.append(
                DatasetExample(
                    question=(
                        f"Show {first.name} "
                        f"and {second.name} "
                        f"from {table.name}"
                    ),
                    sql=(
                        f"SELECT {first.name}, "
                        f"{second.name} "
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

        for column in self._measure_columns(table):
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

        for column in self._measure_columns(table):
            for label, function in self.AGGREGATE_TEMPLATES:
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

        measure_columns = self._measure_columns(table)
        group_columns = self._group_columns(table)

        for group_column in group_columns:
            for measure_column in measure_columns:
                examples.append(
                    DatasetExample(
                        question=(
                            f"What is the average {measure_column.name} "
                            f"by {group_column.name} "
                            f"in {table.name}?"
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

        for column in self._measure_columns(table):
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

    def _generate_join_examples(
        self,
        schema: DatabaseSchema,
    ) -> list[DatasetExample]:
        examples = []

        for table in schema:
            for foreign_key in table.foreign_keys:
                join_data = self._build_join_data(
                    schema=schema,
                    source_table=table.name,
                    foreign_key=foreign_key,
                )

                if join_data is None:
                    continue

                (
                    source_column,
                    target_column,
                    join_conditions,
                ) = join_data

                examples.append(
                    DatasetExample(
                        question=(
                            f"Show {table.name} and "
                            f"{foreign_key.target_table} information"
                        ),
                        sql=(
                            f"SELECT {table.name}.{source_column.name}, "
                            f"{foreign_key.target_table}.{target_column.name} "
                            f"FROM {table.name} "
                            f"JOIN {foreign_key.target_table} "
                            f"ON {join_conditions}"
                        ),
                    )
                )

        return examples

    def _generate_join_filter_examples(
        self,
        schema: DatabaseSchema,
    ) -> list[DatasetExample]:
        examples = []

        for table in schema:
            for foreign_key in table.foreign_keys:
                join_data = self._build_join_data(
                    schema=schema,
                    source_table=table.name,
                    foreign_key=foreign_key,
                )

                if join_data is None:
                    continue

                (
                    source_column,
                    target_column,
                    join_conditions,
                ) = join_data

                source_model = schema.get_table(table.name)

                if source_model is None:
                    continue

                filter_column = next(
                    iter(self._measure_columns(source_model)),
                    None,
                )

                if filter_column is None:
                    continue

                examples.append(
                    DatasetExample(
                        question=(
                            f"Show {table.name} and "
                            f"{foreign_key.target_table} "
                            f"where {filter_column.name} "
                            f"is greater than 50000"
                        ),
                        sql=(
                            f"SELECT {table.name}.{source_column.name}, "
                            f"{foreign_key.target_table}.{target_column.name} "
                            f"FROM {table.name} "
                            f"JOIN {foreign_key.target_table} "
                            f"ON {join_conditions} "
                            f"WHERE {table.name}.{filter_column.name} > 50000"
                        ),
                    )
                )

        return examples

    def _build_join_data(
        self,
        *,
        schema: DatabaseSchema,
        source_table: str,
        foreign_key,
    ):
        target_table = foreign_key.target_table

        source_model = schema.get_table(source_table)
        target_model = schema.get_table(target_table)

        if source_model is None or target_model is None:
            return None

        source_column = self._first_descriptive_column(
            source_model,
            excluded_names=set(foreign_key.source_columns),
        )

        target_column = self._first_descriptive_column(
            target_model,
            excluded_names=set(foreign_key.target_columns),
        )

        if source_column is None or target_column is None:
            return None

        join_conditions = " AND ".join(
            f"{source_table}.{source_name} = "
            f"{target_table}.{target_name}"
            for source_name, target_name in zip(
                foreign_key.source_columns,
                foreign_key.target_columns,
            )
        )

        return (
            source_column,
            target_column,
            join_conditions,
        )

    def _first_descriptive_column(
        self,
        table: Table,
        *,
        excluded_names: set[str],
    ):
        return next(
            (
                column
                for column in table.columns
                if (
                    column.name not in excluded_names
                    and not self._is_identifier_column(column)
                )
            ),
            None,
        )

    def _measure_columns(
        self,
        table: Table,
    ) -> list:
        return [
            column
            for column in table.columns
            if (
                self._is_numeric_column(column)
                and not self._is_identifier_column(column)
            )
        ]

    def _group_columns(
        self,
        table: Table,
    ) -> list:
        return [
            column
            for column in table.columns
            if (
                not column.is_primary_key
                and (
                    self._is_identifier_column(column)
                    or not self._is_numeric_column(column)
                )
            )
        ]

    def _is_numeric_column(
        self,
        column,
    ) -> bool:
        return (
            column.data_type.upper()
            in self.NUMERIC_TYPES
        )

    def _is_identifier_column(
        self,
        column,
    ) -> bool:
        return (
            column.is_primary_key
            or column.is_foreign_key
            or column.name.lower().endswith("_id")
        )