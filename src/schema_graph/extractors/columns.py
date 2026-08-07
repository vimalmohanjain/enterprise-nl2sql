from sqlglot import expressions as exp
from .base import BaseExtractor
from ..models import Column
from ..context import CreateTableContext

class ColumnExtractor(BaseExtractor):
    def extract(
        self,
        contexts: list[CreateTableContext],
    ) -> None:
        for ctx in contexts:
            for column_def in ctx.create.find_all(exp.ColumnDef):
                ctx.table.columns.append(
                    Column(
                        name=column_def.this.name,
                        data_type=column_def.kind.sql()
                    )
                )