import networkx as nx
from .models import DatabaseSchema


class GraphBuilder:
    """Build a lightweight table graph from a parsed schema."""

    def build(self, schema: DatabaseSchema) -> nx.MultiDiGraph:
        graph: nx.MultiDiGraph = nx.MultiDiGraph()

        # Add table and column nodes
        for table_name, table in schema.tables.items():
            graph.add_node(
                table_name,
                node_type="table",
            )

            for column in table.columns:
                column_node = f"{table_name}.{column.name}"

                graph.add_node(
                    column_node,
                    node_type="column",
                    name=column.name,
                    data_type=column.data_type,
                    nullable=column.nullable,
                    is_primary_key=column.is_primary_key,
                    is_foreign_key=column.is_foreign_key,
                    is_unique=column.is_unique,
                )

                graph.add_edge(
                    table_name,
                    column_node,
                    relationship="HAS_COLUMN",
                )

        # Add foreign-key relationships
        for table_name, table in schema.tables.items():
            for foreign_key in table.foreign_keys:
                graph.add_edge(
                    table_name,
                    foreign_key.target_table,
                    relationship="FOREIGN_KEY",
                    source_columns=foreign_key.source_columns,
                    target_columns=foreign_key.target_columns,
                )

        return graph