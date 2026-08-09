import re

from src.schema_graph.models import DatabaseSchema, Table


class TrainingSchemaPruner:
    """Prune a schema to tables referenced by gold SQL."""

    def prune(
        self,
        *,
        schema: DatabaseSchema,
        gold_sql: str,
    ) -> DatabaseSchema:
        required_tables = self._extract_table_names(gold_sql)

        pruned = DatabaseSchema()

        for table_name in required_tables:
            table = schema.get_table(table_name)

            if table is None:
                continue

            pruned.add_table(
                self._copy_table_with_valid_foreign_keys(
                    table=table,
                    required_tables=required_tables,
                )
            )

        return pruned

    def _extract_table_names(
        self,
        sql: str,
    ) -> set[str]:
        pattern = (
            r"\b(?:FROM|JOIN)\s+"
            r'[`"\[]?([A-Za-z_][A-Za-z0-9_]*)'
        )

        return {
            match
            for match in re.findall(
                pattern,
                sql,
                flags=re.IGNORECASE,
            )
        }

    def _copy_table_with_valid_foreign_keys(
        self,
        *,
        table: Table,
        required_tables: set[str],
    ) -> Table:
        return Table(
            name=table.name,
            columns=list(table.columns),
            foreign_keys=[
                foreign_key
                for foreign_key in table.foreign_keys
                if foreign_key.target_table in required_tables
            ],
        )