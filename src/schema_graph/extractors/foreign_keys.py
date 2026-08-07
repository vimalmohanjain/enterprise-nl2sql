from ..models import ForeignKey
from ..context import CreateTableContext
from .base import BaseExtractor
from sqlglot import expressions as exp

class ForeignKeyExtractor(BaseExtractor):
    def extract(self, contexts):
        for ctx in contexts:
            for fk in ctx.create.find_all(exp.ForeignKey):
                source_columns = [
                    identifier.name
                    for identifier in fk.args.get("expressions", [])
                ]

                reference = fk.args.get("reference")
                if reference is None:
                    continue
                schema = reference.this
                target_table = schema.this.name
                target_columns = [
                    identifier.name
                    for identifier in schema.args.get("expressions", [])
                ]
                ctx.table.add_foreign_key(
                    ForeignKey(
                        source_columns=source_columns,
                        target_table=target_table,
                        target_columns=target_columns,
                    )
                )
