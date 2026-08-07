from abc import ABC, abstractmethod
from sqlglot import expressions as exp
from .base import BaseExtractor
from ..context import CreateTableContext

class ColumnPrimaryKeyExtractor(BaseExtractor):
    def extract(self, contexts: CreateTableContext):
        """Extract primary key information from the given context."""
        for ctx in contexts:
            for column_def in ctx.create.find_all(exp.ColumnDef):
                column = ctx.table.get_column(column_def.this.name)
                if column is None:
                    continue
                for constraint in column_def.args.get("constraints", []):
                    if isinstance(
                        constraint.kind,
                        exp.PrimaryKeyColumnConstraint,
                    ):
                        column.is_primary_key = True

class TablePrimaryKeyExtractor(BaseExtractor):
    def extract(self, contexts: CreateTableContext) -> None:
        """Extract primary key information from the given context."""
        for ctx in contexts:
            pk = ctx.create.find(exp.PrimaryKey)
            if pk is None:
                continue
            for identifier in pk.expressions:
                column = ctx.table.get_column(identifier.name)
                if column:
                    column.is_primary_key = True

