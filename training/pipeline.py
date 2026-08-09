from src.schema_graph.models import DatasetExample

from .formatter import TrainingFormatter
from .split import split_dataset


# Raw DatasetExample objects
#           ↓
#    reproducible split
#        ↙       ↘
#     80%         20%
#    train     validation
#      ↓           ↓
#  TrainingFormatter
#      ↓           ↓
# schema + question + correct SQL

class TrainingPipeline:
    """Prepare NL2SQL examples for fine-tuning."""

    def __init__(
        self,
        validation_ratio: float = 0.1,
        seed: int = 42,
    ):
        self.validation_ratio = validation_ratio
        self.seed = seed
        self.formatter = TrainingFormatter()

    def prepare(
        self,
        examples: list[DatasetExample],
        schema_context: str,
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        train_examples, validation_examples = split_dataset(
            examples,
            validation_ratio=self.validation_ratio,
            seed=self.seed,
        )

        train = [
            self.formatter.format(
                example,
                schema_context=schema_context,
            )
            for example in train_examples
        ]

        validation = [
            self.formatter.format(
                example,
                schema_context=schema_context,
            )
            for example in validation_examples
        ]

        return train, validation