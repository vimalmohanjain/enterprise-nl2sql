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
            "text": prompt + completion,
        }

    def format_with_plan(
        self,
        example: DatasetExample,
        *,
        schema_context: str,
        plan: str,
    ) -> dict[str, str]:
        prompt = (
            "You are given the following database schema:\n\n"
            f"{schema_context}\n\n"
            "Question:\n"
            f"{example.question}\n\n"
            "Generate a structured SQL plan followed by SQL.\n\n"
            "Response:\n"
        )

        completion = (
            "<plan>\n"
            f"{plan}\n"
            "</plan>\n"
            "<sql>\n"
            f"{example.sql}\n"
            "</sql>"
        )

        return {
            "instruction": example.question,
            "schema_context": schema_context,
            "output": example.sql,
            "plan": plan,
            "prompt": prompt,
            "completion": completion,
            "text": prompt + completion,
        }