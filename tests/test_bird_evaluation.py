import sqlite3
from training.bird_database import BirdDatabaseResolver
from training.bird_evaluation import (
    BirdEvaluationExample,
    BirdExecutionEvaluator,
)

def test_bird_evaluation_example_contains_database_id():
    example = BirdEvaluationExample(
        db_id="movie_platform",
        question="How many movies were released in 2007?",
        expected_sql="SELECT COUNT(*) FROM movies WHERE movie_release_year = 2007",
    )

    assert example.db_id == "movie_platform"
    assert example.question == "How many movies were released in 2007?"
    assert example.expected_sql.startswith("SELECT")

from src.schema_graph.models import BirdTrainingExample, DatabaseSchema
from training.bird_evaluation import build_bird_evaluation_split


def test_build_bird_evaluation_split_preserves_db_id():
    schema = DatabaseSchema()

    examples = [
        BirdTrainingExample(
            db_id=f"db_{index}",
            question=f"Question {index}",
            sql=f"SELECT {index}",
            schema=schema,
        )
        for index in range(10)
    ]

    validation = build_bird_evaluation_split(
        examples,
        validation_ratio=0.2,
        seed=42,
    )

    assert len(validation) == 2
    assert all(example.db_id.startswith("db_") for example in validation)
    assert all(example.expected_sql.startswith("SELECT") for example in validation)




def test_bird_execution_evaluator_uses_correct_database(tmp_path):
    db_root = tmp_path / "train_databases"
    db_dir = db_root / "company"
    db_dir.mkdir(parents=True)

    db_path = db_dir / "company.sqlite"

    connection = sqlite3.connect(db_path)
    connection.execute(
        "CREATE TABLE employees (name TEXT)"
    )
    connection.execute(
        "INSERT INTO employees VALUES ('Alice')"
    )
    connection.commit()
    connection.close()

    example = BirdEvaluationExample(
        db_id="company",
        question="Show employee names",
        expected_sql="SELECT name FROM employees",
    )

    resolver = BirdDatabaseResolver(db_root)

    evaluator = BirdExecutionEvaluator(
        database_resolver=resolver,
    )

    assert evaluator.evaluate(
        example=example,
        predicted_sql="SELECT name FROM employees;",
    ) is True

from training.bird_evaluation import BirdEvaluationPipeline


class FakeInference:
    def generate(self, prompt: str) -> str:
        return "SELECT name FROM employees;"


class FakeExecutionEvaluator:
    def evaluate(self, *, example, predicted_sql):
        return True


def test_bird_evaluation_pipeline_evaluates_example():
    example = BirdEvaluationExample(
        db_id="company",
        question="Show employee names",
        expected_sql="SELECT name FROM employees",
    )

    pipeline = BirdEvaluationPipeline(
        inference=FakeInference(),
        execution_evaluator=FakeExecutionEvaluator(),
    )

    results = pipeline.evaluate(
        [example],
        prompt_builder=lambda example: example.question,
    )

    assert len(results) == 1

    result = results[0]

    assert result.question == "Show employee names"
    assert result.predicted_sql == "SELECT name FROM employees;"
    assert result.strict_match is True
    assert result.execution_match is True

