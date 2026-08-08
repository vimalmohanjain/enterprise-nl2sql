from .models import DatabaseSchema


class SchemaRetriever:
    """Retrieve schema information from a DatabaseSchema object."""

    def retrieve(
        self,
        question: str,
        schema: DatabaseSchema,
        graph: nx.MultiDiGraph
    ) -> set[str]:
        """Return table names relevant to the question."""

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

        return relevant_tables