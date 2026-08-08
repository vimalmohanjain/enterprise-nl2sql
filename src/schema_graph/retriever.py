import networkx as nx
from .models import DatabaseSchema, ForeignKey, RetrievalResult

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

        relevant_tables = {
            table.name
            for table in schema
            if (
                table.name.lower() in question_lower
                or any(
                    column.name.lower() in question_lower
                    for column in table.columns
                )
            )
        }

        tables_to_visit = set(relevant_tables)
        for _ in range(max_hops):
            next_tables = set()
            for table in tables_to_visit:
                next_tables.update(graph.successors(table))
            next_tables.difference_update(relevant_tables)
            relevant_tables.update(next_tables)
            tables_to_visit = next_tables

            if not tables_to_visit:
                break
        print("QUESTION:", question_lower)

        for table in schema:
            print(
                "TABLE:",
                table.name,
                "COLUMNS:",
                [column.name for column in table.columns],
            )

        print("DIRECT MATCHES:", relevant_tables)

        relationships: list[ForeignKey] = []
        for source_table in relevant_tables:
            for target_table in graph.successors(source_table):
                if target_table not in relevant_tables:
                    continue
                edge_data = graph.get_edge_data(source_table, target_table)

                for edge in edge_data.values():
                    relationships.append(
                        ForeignKey(
                            source_columns=edge["source_columns"],
                            target_table=target_table,
                            target_columns=edge["target_columns"],
                        )
                    )
                
        return RetrievalResult(tables=relevant_tables, relationships=relationships)