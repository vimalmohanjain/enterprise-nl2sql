from src.schema_graph.models import DatasetExample


class TrainingFormatter:
    """Convert dataset examples into fine-tuning records."""

    def format(
        self,
        example: DatasetExample,
        schema_context: str = "",
    ) -> dict[str, str]:
        prompt = (
            "You are given the following database schema:\n\n"
            f"{schema_context}\n\n"
            "Question:\n"
            f"{example.question}\n\n"
            "Generate SQL only.\n\n"
            "SQL:\n"
        )

        completion = example.sql

        return {
            "instruction": example.question,
            "schema_context": schema_context,
            "output": example.sql,
            "prompt": prompt,
            "completion": completion,
            # Keep Experiment 1 compatibility for now.
            "text": prompt + completion,
        }