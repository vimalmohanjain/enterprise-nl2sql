import sqlite3
from dataclasses import dataclass

from src.schema_graph.evaluator import SQLEvaluator
from src.schema_graph.models import BirdTrainingExample
from training.bird_database import BirdDatabaseResolver
from training.split import split_dataset


@dataclass(slots=True)
class BirdEvaluationExample:
    db_id: str
    question: str
    expected_sql: str


def build_bird_evaluation_split(
    examples: list[BirdTrainingExample],
    *,
    validation_ratio: float = 0.1,
    seed: int = 42,
) -> list[BirdEvaluationExample]:
    _, validation_examples = split_dataset(
        examples,
        validation_ratio=validation_ratio,
        seed=seed,
    )

    return [
        BirdEvaluationExample(
            db_id=example.db_id,
            question=example.question,
            expected_sql=example.sql,
        )
        for example in validation_examples
    ]


class BirdExecutionEvaluator:
    """Evaluate generated SQL against the correct BIRD database."""

    def __init__(
        self,
        *,
        database_resolver: BirdDatabaseResolver,
        sql_evaluator: SQLEvaluator | None = None,
    ):
        self.database_resolver = database_resolver
        self.sql_evaluator = sql_evaluator or SQLEvaluator()

    def evaluate(
        self,
        *,
        example: BirdEvaluationExample,
        predicted_sql: str,
    ) -> bool:
        database_path = self.database_resolver.resolve(
            example.db_id
        )

        with sqlite3.connect(database_path) as connection:
            return self.sql_evaluator.evaluate_execution(
                predicted_sql=predicted_sql,
                expected_sql=example.expected_sql,
                connection=connection,
            )

from src.schema_graph.models import EvaluationDetail


class BirdEvaluationPipeline:
    """Run strict and execution evaluation for BIRD examples."""

    def __init__(
        self,
        *,
        inference,
        execution_evaluator,
        sql_evaluator: SQLEvaluator | None = None,
    ):
        self.inference = inference
        self.execution_evaluator = execution_evaluator
        self.sql_evaluator = sql_evaluator or SQLEvaluator()

    def evaluate(
        self,
        examples: list[BirdEvaluationExample],
        *,
        prompt_builder,
    ) -> list[EvaluationDetail]:
        results = []

        for example in examples:
            prompt = prompt_builder(example)

            predicted_sql = self.inference.generate(prompt)

            results.append(
                EvaluationDetail(
                    question=example.question,
                    expected_sql=example.expected_sql,
                    predicted_sql=predicted_sql,
                    strict_match=self.sql_evaluator.evaluate(
                        predicted_sql=predicted_sql,
                        expected_sql=example.expected_sql,
                    ),
                    execution_match=self.execution_evaluator.evaluate(
                        example=example,
                        predicted_sql=predicted_sql,
                    ),
                )
            )

        return results