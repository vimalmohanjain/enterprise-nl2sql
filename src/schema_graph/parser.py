import sqlglot
from sqlglot import expressions as exp
from pathlib import Path
from os import PathLike, path
from .context import CreateTableContext
from .extractors import (
    ColumnExtractor,
    ColumnPrimaryKeyExtractor,
    TablePrimaryKeyExtractor,
)

from .models import (
    DatabaseSchema,
    Table,
    Column,
)

class SchemaParser:
    def __init__(self):
        self.extractors = (
            ColumnExtractor(),
            ColumnPrimaryKeyExtractor(),
            TablePrimaryKeyExtractor(),
        )

    def parse(self, sql: str) -> DatabaseSchema:
        statements = sqlglot.parse(sql)
        contexts = self._build_contexts(statements)

        for extractor in self.extractors:
            extractor.extract(contexts)

        return DatabaseSchema(
            tables={
                ctx.table.name: ctx.table
                for ctx in contexts
            }
        )

    def parse_file(self, path: str | PathLike) -> DatabaseSchema:
        """
        Parse a SQL DDL file into a DatabaseSchema.
        """
        sql = Path(path).read_text(encoding="utf-8")
        return self.parse(sql)

    def _build_contexts(self, statements):
        contexts = []
        for statement in statements:
            if not isinstance(statement, exp.Create):
                continue

            table = statement.find(exp.Table)
            if table is None:
                continue

            contexts.append(
                CreateTableContext(
                    create=statement,
                    table_expr=table,
                    table=Table(name=table.name),
                )
            )
        return contexts
