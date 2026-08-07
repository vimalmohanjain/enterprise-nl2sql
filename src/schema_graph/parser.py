import sqlglot
from sqlglot import expressions as exp
from src.schema_graph.models import SchemaMetadata, Table

from pathlib import Path

class SchemaParser:
    """Parses SQL DDL into SchemaMetadata."""

    def parse_file(self, file_path: str | Path) -> SchemaMetadata:
        """Parse a SQL file."""
        file_path = Path(file_path)

        with file_path.open("r", encoding="utf-8") as f:
            sql = f.read()

        return self.parse_sql(sql)

    def parse_sql(self, sql: str) -> SchemaMetadata:
        """Parse SQL string into SchemaMetadata."""
        schema = SchemaMetadata()
        statements = sqlglot.parse(sql)
        for statement in statements:
            if not isinstance(statement, exp.Create):
                continue

            table = statement.find(exp.Table)
            if table is None:
                continue
            schema.add_table(Table(name=table.name))
        return schema

if __name__ == "__main__":
    parser = SchemaParser()

    try:
        parser.parse_file("data/schemas/company.sql")
    except NotImplementedError:
        print("Parser skeleton is working.")