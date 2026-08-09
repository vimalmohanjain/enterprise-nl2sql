from src.schema_graph.models import DatasetExample


class TrainingFormatter:
    """Convert dataset examples into fine-tuning records."""

    def format(
        self,
        example: DatasetExample,
        schema_context: str = "",
    ) -> dict[str, str]:
        text = (
            "You are given the following database schema:\n\n"
            f"{schema_context}\n\n"
            "Question:\n"
            f"{example.question}\n\n"
            "Generate SQL only.\n\n"
            "SQL:\n"
            f"{example.sql}"
        )

        return {
            "instruction": example.question,
            "schema_context": schema_context,
            "output": example.sql,
            "text": text,
        }