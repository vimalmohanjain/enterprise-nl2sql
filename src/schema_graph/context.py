from dataclasses import dataclass
from sqlglot import expressions as exp
from .models import Table


@dataclass(slots=True)
class CreateTableContext:
    create: exp.Create
    table: Table