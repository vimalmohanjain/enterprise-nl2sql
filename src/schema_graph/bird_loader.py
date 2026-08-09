import json
from pathlib import Path
from .models import (
    Column,
    DatabaseSchema,
    DatasetExample,
    ForeignKey,
    Table,
)


class BirdDatasetLoader:
    """Load NL2SQL examples from the BIRD training dataset."""

    def load_examples(
        self,
        path: str | Path,
    ) -> list[DatasetExample]:
        path = Path(path)

        records = json.loads(
            path.read_text(encoding="utf-8")
        )

        return [
            DatasetExample(
                question=record["question"],
                sql=record["SQL"],
            )
            for record in records
        ]

    def load_schema(
        self,
        path: str | Path,
        *,
        db_id: str,
    ) -> dict:
        path = Path(path)

        schemas = json.loads(
            path.read_text(encoding="utf-8")
        )

        for schema in schemas:
            if schema["db_id"] == db_id:
                return schema

        raise ValueError(
            f"BIRD schema not found for database: {db_id}"
        )

    def convert_schema(
        self,
        bird_schema: dict,
    ) -> DatabaseSchema:
        schema = DatabaseSchema()

        # 1. Create the tables.
        tables = []

        for table_name in bird_schema["table_names_original"]:
            table = Table(name=table_name)
            schema.add_table(table)
            tables.append(table)

        column_names = bird_schema["column_names_original"]
        column_types = bird_schema["column_types"]

        primary_keys = self._primary_key_indexes(
            bird_schema["primary_keys"]
        )

        # Keep BIRD column index -> Column mapping.
        columns_by_index = {}

        # 2. Create the columns.
        for column_index, (
            column_definition,
            data_type,
        ) in enumerate(
            zip(column_names, column_types)
        ):
            table_index, column_name = column_definition

            # BIRD's "*" pseudo-column is not a real column.
            if table_index == -1:
                continue

            column = Column(
                name=column_name,
                data_type=data_type,
                is_primary_key=column_index in primary_keys,
            )

            tables[table_index].add_column(column)

            columns_by_index[column_index] = column

        # 3. Convert foreign keys.
        for source_index, target_index in bird_schema["foreign_keys"]:
            source_table_index, source_column_name = (
                column_names[source_index]
            )

            target_table_index, target_column_name = (
                column_names[target_index]
            )

            source_table = tables[source_table_index]
            target_table = tables[target_table_index]

            source_column = columns_by_index[source_index]
            source_column.is_foreign_key = True

            foreign_key = ForeignKey(
                source_columns=[source_column_name],
                target_table=target_table.name,
                target_columns=[target_column_name],
            )

            source_table.add_foreign_key(foreign_key)

        return schema

    def _primary_key_indexes(
        self,
        primary_keys: list,
    ) -> set[int]:
        indexes = set()

        for key in primary_keys:
            if isinstance(key, list):
                indexes.update(key)
            else:
                indexes.add(key)

        return indexes