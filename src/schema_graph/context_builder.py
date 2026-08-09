from .models import DatabaseSchema, TableContext, SchemaContext, Relationship
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

    def build_full(
        self,
        schema: DatabaseSchema,
    ) -> SchemaContext:
        tables = {
            table.name: TableContext(
                name=table.name,
                columns={
                    column.name: column
                    for column in table.columns
                },
            )
            for table in schema
        }

        relationships = []

        for table in schema:
            for foreign_key in table.foreign_keys:
                relationships.append(
                    Relationship(
                        source_table=table.name,
                        target_table=foreign_key.target_table,
                        source_columns=foreign_key.source_columns,
                        target_columns=foreign_key.target_columns,
                    )
                )

        return SchemaContext(
            tables=tables,
            relationships=relationships,
        )