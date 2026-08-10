from src.schema_graph.models import DatasetExample
from training.pipeline import TrainingPipeline


def test_training_pipeline_prepares_dataset():
    examples = [
        DatasetExample(
            question=f"Question {i}",
            sql=f"SELECT {i}",
        )
        for i in range(10)
    ]

    pipeline = TrainingPipeline(
        validation_ratio=0.2,
        seed=42,
    )

    train, validation = pipeline.prepare(
        examples=examples,
        schema_context="Table: employees",
    )

    assert len(train) == 8
    assert len(validation) == 2

    assert all("text" in record for record in train)
    assert all("text" in record for record in validation)

    assert all(
        "Table: employees" in record["text"]
        for record in train + validation
    )
    assert all("prompt" in record for record in train)
    assert all("completion" in record for record in train)

    assert all("prompt" in record for record in validation)
    assert all("completion" in record for record in validation)