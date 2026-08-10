import numpy as np

from src.schema_graph.models import (
    Column,
    DatabaseSchema,
    Table,
)
from training.semantic_ranker import (
    SentenceTransformerTableRanker,
)


def test_semantic_ranker_orders_tables_by_similarity():
    schema = DatabaseSchema()

    schema.add_table(
        Table(
            name="orders",
            columns=[
                Column(
                    name="order_id",
                    data_type="integer",
                )
            ],
        )
    )

    schema.add_table(
        Table(
            name="shippers",
            columns=[
                Column(
                    name="company_name",
                    data_type="text",
                )
            ],
        )
    )

    class FakeModel:
        def encode(
            self,
            texts,
            normalize_embeddings=True,
        ):
            if len(texts) == 1:
                return np.array([
                    [1.0, 0.0],
                ])

            return np.array([
                [0.2, 0.8],  # orders
                [0.9, 0.1],  # shippers
            ])

    ranker = SentenceTransformerTableRanker(
        model=FakeModel(),
    )

    ranked = ranker.rank(
        "Which shipping company is used most often?",
        schema,
    )

    assert ranked == [
        "shippers",
        "orders",
    ]