from src.schema_graph.graph_builder import GraphBuilder
from src.schema_graph.models import (
    Column,
    DatabaseSchema,
    Table,
)
from src.schema_graph.retriever import SchemaRetriever
from training.semantic_retriever import SemanticSchemaRetriever


def test_semantic_retriever_adds_top_ranked_table():
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

    schema.add_table(
        Table(
            name="products",
            columns=[
                Column(
                    name="product_name",
                    data_type="text",
                )
            ],
        )
    )

    graph = GraphBuilder().build(schema)

    class FakeSemanticRanker:
        def rank(
            self,
            question,
            schema,
        ):
            return [
                "shippers",
                "orders",
                "products",
            ]

    retriever = SemanticSchemaRetriever(
        base_retriever=SchemaRetriever(),
        semantic_ranker=FakeSemanticRanker(),
        top_k=2,
    )

    result = retriever.retrieve(
        question="What shipping company is used most often?",
        schema=schema,
        graph=graph,
        max_hops=0,
    )

    assert "shippers" in result.tables
    assert "orders" in result.tables
    assert "products" not in result.tables