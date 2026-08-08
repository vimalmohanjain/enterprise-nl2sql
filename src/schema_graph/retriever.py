import networkx as nx
from .models import DatabaseSchema, Relationship, RetrievalResult

class SchemaRetriever:
    """Retrieve schema information from a DatabaseSchema object."""

    def retrieve(
        self,
        question: str,
        schema: DatabaseSchema,
        graph: nx.MultiDiGraph,
        max_hops: int = 1,
    ) -> RetrievalResult:
        """Return table names and relationships relevant to the question."""
        if max_hops < 0:
            raise ValueError("max_hops must be non-negative")
        
        question_lower = question.lower()

        relevant_tables = set()

        for table in schema:
            table_name = table.name.lower()

            table_matches = (
                table_name in question_lower
                or (
                    table_name.endswith("s")
                    and table_name[:-1] in question_lower
                )
            )

            column_matches = any(
                column.name.lower() in question_lower
                for column in table.columns
            )

            if table_matches or column_matches:
                relevant_tables.add(table.name)

        tables_to_visit = set(relevant_tables)
        for _ in range(max_hops):
            next_tables = set()
            for table in tables_to_visit:
                for _, target, edge_data in graph.out_edges(
                    table,
                    data=True,
                ):
                    if edge_data.get("relationship") == "FOREIGN_KEY":
                        next_tables.add(target)
            next_tables.difference_update(relevant_tables)
            relevant_tables.update(next_tables)
            tables_to_visit = next_tables

            if not tables_to_visit:
                break

        relationships: list[Relationship] = []
        for source_table in relevant_tables:
            for target_table in graph.successors(source_table):
                if target_table not in relevant_tables:
                    continue
                edge_data = graph.get_edge_data(source_table, target_table)

                for edge in edge_data.values():
                    if edge.get("relationship") != "FOREIGN_KEY":
                        continue

                    relationships.append(
                        Relationship(
                            source_table=source_table,
                            target_table=target_table,
                            source_columns=edge["source_columns"],
                            target_columns=edge["target_columns"],
                        )
                    )
                
        return RetrievalResult(tables=relevant_tables, relationships=relationships)