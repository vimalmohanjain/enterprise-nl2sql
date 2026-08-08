import networkx as nx
from .models import DatabaseSchema

class GraphBuilder:
    """Build a lightweight table graph from a parsed schema."""

    def build(self, schema: DatabaseSchema) -> dict[str, list[ForeignKey]]:
        graph: nx.MultiDiGraph = nx.MultiDiGraph()

        for table_name in schema.tables:
            graph.add_node(table_name)

        for table_name, table in schema.tables.items():
            for foreign_key in table.foreign_keys:
                graph.add_edge(
                    table_name,
                    foreign_key.target_table,
                    source_columns=foreign_key.source_columns,
                    target_columns=foreign_key.target_columns,
                    )
        return graph
