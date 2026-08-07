from .models import DatabaseSchema, ForeignKey


class GraphBuilder:
    """Build a lightweight table graph from a parsed schema."""

    def build(self, schema: DatabaseSchema) -> dict[str, dict[str, ForeignKey]]:
        graph: dict[str, dict[str, ForeignKey]] = {}

        for table_name, table in schema.tables.items():
            graph[table_name] = {
                foreign_key.target_table: foreign_key
                for foreign_key in table.foreign_keys
            }

        return graph
