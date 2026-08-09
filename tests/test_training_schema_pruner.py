from src.schema_graph.models import (
    Column,
    DatabaseSchema,
    ForeignKey,
    Table,
)
from training.schema_pruner import TrainingSchemaPruner


def test_training_schema_pruner_keeps_gold_sql_tables():
    schema = DatabaseSchema()

    movies = Table(
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

    ratings = Table(
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
        foreign_keys=[
            ForeignKey(
                source_columns=["movie_id"],
                target_table="movies",
                target_columns=["movie_id"],
            )
        ],
    )

    lists = Table(
        name="lists",
        columns=[
            Column(
                name="list_id",
                data_type="integer",
                is_primary_key=True,
            ),
            Column(
                name="list_title",
                data_type="text",
            ),
        ],
    )

    schema.add_table(movies)
    schema.add_table(ratings)
    schema.add_table(lists)

    pruner = TrainingSchemaPruner()

    pruned = pruner.prune(
        schema=schema,
        gold_sql=(
            "SELECT movies.movie_title "
            "FROM movies "
            "JOIN ratings "
            "ON ratings.movie_id = movies.movie_id"
        ),
    )

    assert set(pruned.tables) == {
        "movies",
        "ratings",
    }

    assert pruned.get_table("lists") is None

    ratings_table = pruned.get_table("ratings")

    assert ratings_table is not None
    assert len(ratings_table.foreign_keys) == 1
