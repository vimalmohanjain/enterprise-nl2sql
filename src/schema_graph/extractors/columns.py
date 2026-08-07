from collections.abc import Iterable
from sqlglot import expressions as exp
from .base import BaseExtractor
from ..models import Column
from ..context import CreateTableContext

class ColumnExtractor(BaseExtractor):
    def extract(
        self,
        contexts: Iterable[CreateTableContext],
    ) -> None:
        for ctx in contexts:
            for column_def in ctx.create.find_all(exp.ColumnDef):
                ctx.table.add_column(
                    Column(
                        name=column_def.this.name,
                        data_type=column_def.kind.sql()
                    )
                )