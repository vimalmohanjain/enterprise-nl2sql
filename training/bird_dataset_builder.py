from src.schema_graph.context_builder import ContextBuilder
from src.schema_graph.models import (
    BirdTrainingExample,
    DatasetExample,
)
from src.schema_graph.prompt_builder import PromptBuilder

from .formatter import TrainingFormatter
from .schema_pruner import TrainingSchemaPruner
from .sql_plan import SQLPlanBuilder


class BirdTrainingDatasetBuilder:
    """Build schema-aware fine-tuning records from BIRD examples."""

    def __init__(
        self,
        *,
        tokenizer,
        max_length: int = 2048,
        include_sql_plan: bool = False,
    ):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.include_sql_plan = include_sql_plan

        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()
        self.formatter = TrainingFormatter()
        self.pruner = TrainingSchemaPruner()
        self.plan_builder = SQLPlanBuilder()

    def build(
        self,
        examples: list[BirdTrainingExample],
    ) -> list[dict[str, str]]:
        records = []

        for example in examples:
            record = self._format_with_schema(
                example=example,
                schema=example.schema,
            )

            token_count = len(
                self.tokenizer.encode(
                    record["text"],
                    add_special_tokens=True,
                )
            )

            if token_count > self.max_length:
                pruned_schema = self.pruner.prune(
                    schema=example.schema,
                    gold_sql=example.sql,
                )

                record = self._format_with_schema(
                    example=example,
                    schema=pruned_schema,
                )

            record["completion"] += (
                self.tokenizer.eos_token
            )

            records.append(record)

        return records

    def _format_with_schema(
        self,
        *,
        example: BirdTrainingExample,
        schema,
    ) -> dict[str, str]:
        context = self.context_builder.build_full(
            schema
        )

        schema_text = (
            self.prompt_builder.build_schema_context(
                context
            )
        )

        dataset_example = DatasetExample(
            question=example.question,
            sql=example.sql,
        )

        if not self.include_sql_plan:
            return self.formatter.format(
                dataset_example,
                schema_context=schema_text,
            )

        plan = self.plan_builder.build(
            example.sql
        )

        return self.formatter.format_with_plan(
            dataset_example,
            schema_context=schema_text,
            plan=plan,
        )