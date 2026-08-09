from src.schema_graph.models import EvaluationDetail
from pathlib import Path

from src.schema_graph.bird_loader import BirdDatasetLoader
from training.bird_evaluation import build_bird_evaluation_split

def summarize_results(
    results: list[EvaluationDetail],
) -> dict[str, float | int]:
    total = len(results)

    strict_correct = sum(
        result.strict_match
        for result in results
    )

    execution_correct = sum(
        result.execution_match
        for result in results
    )

    return {
        "total": total,
        "strict_correct": strict_correct,
        "execution_correct": execution_correct,
        "strict_accuracy": (
            strict_correct / total
            if total
            else 0.0
        ),
        "execution_accuracy": (
            execution_correct / total
            if total
            else 0.0
        ),
    }

def run_evaluation(
    *,
    pipeline,
    examples,
    prompt_builder,
):
    results = pipeline.evaluate(
        examples,
        prompt_builder=prompt_builder,
    )

    summary = summarize_results(results)

    return results, summary

def load_validation_examples(
    *,
    train_file: str | Path,
    tables_file: str | Path,
    validation_ratio: float = 0.1,
    seed: int = 42,
):
    loader = BirdDatasetLoader()

    training_examples = loader.load_training_examples(
        train_file=train_file,
        tables_file=tables_file,
    )

    return build_bird_evaluation_split(
        training_examples,
        validation_ratio=validation_ratio,
        seed=seed,
    )