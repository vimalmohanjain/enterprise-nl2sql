from src.schema_graph.models import (
    BirdTrainingExample,
    Column,
    DatabaseSchema,
    Table,
)
from training.bird_dataset_builder import BirdTrainingDatasetBuilder


class FakeTokenizer:
    def encode(
        self,
        text,
        add_special_tokens=True,
    ):
        return text.split()


def test_builder_formats_bird_training_examples():
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="employees",
            columns=[
                Column(
                    name="employee_id",
                    data_type="integer",
                    is_primary_key=True,
                ),
                Column(
                    name="name",
                    data_type="text",
                ),
            ],
        )
    )

    examples = [
        BirdTrainingExample(
            db_id="company",
            question="Show employee names",
            sql="SELECT name FROM employees",
            schema=schema,
        )
    ]

    builder = BirdTrainingDatasetBuilder(
        tokenizer=FakeTokenizer(),
        max_length=2048,
    )

    records = builder.build(examples)

    assert len(records) == 1

    record = records[0]

    assert "employees" in record["text"]
    assert "employee_id" in record["text"]
    assert "Show employee names" in record["text"]
    assert "SELECT name FROM employees" in record["text"]

def test_builder_prunes_oversized_schema():
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="movies",
            columns=[
                Column(
                    name="movie_id",
                    data_type="integer",
                    is_primary_key=True,
                ),
                Column(
                    name="movie_title",
                    data_type="text",
                ),
            ],
        )
    )

    schema.add_table(
        Table(
            name="ratings",
            columns=[
                Column(
                    name="rating_id",
                    data_type="integer",
                    is_primary_key=True,
                ),
                Column(
                    name="movie_id",
                    data_type="integer",
                    is_foreign_key=True,
                ),
            ],
        )
    )

    # Add unrelated tables to make the full schema "large".
    for index in range(20):
        schema.add_table(
            Table(
                name=f"unrelated_{index}",
                columns=[
                    Column(
                        name="id",
                        data_type="integer",
                    ),
                    Column(
                        name="description",
                        data_type="text",
                    ),
                ],
            )
        )

    example = BirdTrainingExample(
        db_id="movies_db",
        question="Show movie titles that have ratings",
        sql=(
            "SELECT movies.movie_title "
            "FROM movies "
            "JOIN ratings "
            "ON ratings.movie_id = movies.movie_id"
        ),
        schema=schema,
    )

    class SmallLimitTokenizer:
        def encode(
            self,
            text,
            add_special_tokens=True,
        ):
            return text.split()

    builder = BirdTrainingDatasetBuilder(
        tokenizer=SmallLimitTokenizer(),
        max_length=40,
    )

    records = builder.build([example])

    assert len(records) == 1

    text = records[0]["text"]

    assert "Table: movies" in text
    assert "Table: ratings" in text

    assert "Table: unrelated_0" not in text
    assert "Table: unrelated_19" not in text