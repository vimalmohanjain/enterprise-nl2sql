from src.schema_graph.context_builder import ContextBuilder
from src.schema_graph.models import (
    BirdTrainingExample,
    DatasetExample,
)
from src.schema_graph.prompt_builder import PromptBuilder

from .formatter import TrainingFormatter
from .schema_pruner import TrainingSchemaPruner


class BirdTrainingDatasetBuilder:
    """Build schema-aware fine-tuning records from BIRD examples."""

    def __init__(
        self,
        *,
        tokenizer,
        max_length: int = 2048,
    ):
        self.tokenizer = tokenizer
        self.max_length = max_length

        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()
        self.formatter = TrainingFormatter()
        self.pruner = TrainingSchemaPruner()

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

            records.append(record)

        return records

    def _format_with_schema(
        self,
        *,
        example: BirdTrainingExample,
        schema,
    ) -> dict[str, str]:
        context = self.context_builder.build_full(schema)

        schema_text = self.prompt_builder.build_schema_context(
            context
        )

        dataset_example = DatasetExample(
            question=example.question,
            sql=example.sql,
        )

        return self.formatter.format(
            dataset_example,
            schema_context=schema_text,
        )