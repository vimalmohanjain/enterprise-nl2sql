import networkx as nx
from .models import DatabaseSchema, ForeignKey, RetrievalResult

class SchemaRetriever:
    """Retrieve schema information from a DatabaseSchema object."""

    def retrieve(
        self,
        question: str,
        schema: DatabaseSchema,
        graph: nx.MultiDiGraph
    ) -> RetrievalResult:
        """Return table names and relationships relevant to the question."""

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

        for table_name in list(relevant_tables):
            relevant_tables.update(graph.successors(table_name))

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