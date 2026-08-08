from .models import DatabaseSchema, ForeignKey


class GraphBuilder:
    """Build a lightweight table graph from a parsed schema."""

    def build(self, schema: DatabaseSchema) -> dict[str, list[ForeignKey]]:
        graph: dict[str, list[ForeignKey]] = {}

        for table_name, table in schema.tables.items():
            graph[table_name] = list(table.foreign_keys)
        return graph
