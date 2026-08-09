from .models import SchemaContext


class PromptBuilder:
    """Build an LLM-ready prompt from schema context."""

    def build_schema_context(
        self,
        context: SchemaContext,
    ) -> str:
        lines = []

        for table_name, table in context.tables.items():
            lines.append(f"Table: {table_name}")
            lines.append("Columns:")

            for column in table.columns.values():
                column_line = f"- {column.name} {column.data_type}"

                if column.is_primary_key:
                    column_line += " PRIMARY KEY"

                if column.is_foreign_key:
                    column_line += " FOREIGN KEY"

                lines.append(column_line)

            lines.append("")

        if context.relationships:
            lines.append("Relationships:")

            for relationship in context.relationships:
                for source_column, target_column in zip(
                    relationship.source_columns,
                    relationship.target_columns,
                ):
                    lines.append(
                        f"{relationship.source_table}.{source_column} "
                        f"-> "
                        f"{relationship.target_table}.{target_column}"
                    )

            lines.append("")

        return "\n".join(lines).strip()

    def build(
        self,
        question: str,
        context: SchemaContext,
    ) -> str:
        schema_text = self.build_schema_context(context)

        lines = [
            "You are given the following database schema:",
            "",
            schema_text,
            "",
            "Question:",
            question,
            "",
            "Generate SQL only.",
        ]

        return "\n".join(lines)