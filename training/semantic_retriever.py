class SemanticSchemaRetriever:
    """Augment deterministic schema retrieval with semantic table seeds."""

    def __init__(
        self,
        *,
        base_retriever,
        semantic_ranker,
        top_k: int = 3,
    ):
        if top_k < 0:
            raise ValueError("top_k must be non-negative")

        self.base_retriever = base_retriever
        self.semantic_ranker = semantic_ranker
        self.top_k = top_k

    def retrieve(
        self,
        question,
        schema,
        graph,
        max_hops: int = 1,
    ):
        ranked_tables = self.semantic_ranker.rank(
            question,
            schema,
        )

        semantic_tables = set(
            ranked_tables[: self.top_k]
        )

        return self.base_retriever.retrieve(
            question=question,
            schema=schema,
            graph=graph,
            max_hops=max_hops,
            extra_tables=semantic_tables,
        )