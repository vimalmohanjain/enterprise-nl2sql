from .models import DatabaseSchema, TableContext, SchemaContext
from .retriever import RetrievalResult

class ContextBuilder:
    """Build an LLM-ready schema context from retrieved schema information."""

    def build(
        self,
        result: RetrievalResult,
        schema: DatabaseSchema,
    ) -> SchemaContext:

        tables = {}

        for table_name in result.tables:
            table = schema.get_table(table_name)

            if table is None:
                continue

            tables[table_name] = TableContext(
                name=table.name,
                columns={
                    column.name: column
                    for column in table.columns
                },
            )

        return SchemaContext(
            tables=tables,
            relationships=list(result.relationships),
        )