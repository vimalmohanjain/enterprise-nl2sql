import sqlglot
from sqlglot import expressions as exp
from pathlib import Path
from os import PathLike
from .context import CreateTableContext
from .extractors import (
    BaseExtractor,
    ColumnExtractor,
    ColumnPrimaryKeyExtractor,
    TablePrimaryKeyExtractor,
)

from .models import (
    DatabaseSchema,
    Table,
)

class SchemaParser:
    def __init__(self):
        self._extractors:tuple[BaseExtractor, ...]  = (
            ColumnExtractor(),
            ColumnPrimaryKeyExtractor(),
            TablePrimaryKeyExtractor(),
        ) 

    def parse(self, sql: str) -> DatabaseSchema:
        statements = sqlglot.parse(sql)
        contexts = self._build_contexts(statements)

        for extractor in self._extractors:
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

    def _build_contexts(self, statements)-> list[CreateTableContext]:
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
