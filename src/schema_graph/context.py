from dataclasses import dataclass

from sqlglot import expressions as exp

from src.schema_graph.models import Table


@dataclass(slots=True)
class CreateTableContext:
    create: exp.Create
    table_expr: exp.Table
    table: Table