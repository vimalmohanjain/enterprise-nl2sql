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
        max_hops: int = 0,
    ):
        result, _ = self.retrieve_with_diagnostics(
            question=question,
            schema=schema,
            graph=graph,
            max_hops=max_hops,
        )

        return result

    def retrieve_with_diagnostics(
        self,
        question,
        schema,
        graph,
        max_hops: int = 0,
    ):
        ranked_tables = self.semantic_ranker.rank(
            question,
            schema,
        )

        semantic_tables = ranked_tables[: self.top_k]

        result = self.base_retriever.retrieve(
            question=question,
            schema=schema,
            graph=graph,
            max_hops=max_hops,
            extra_tables=set(semantic_tables),
        )

        diagnostics = {
            "semantic_tables": list(semantic_tables),
            "final_tables": sorted(result.tables),
        }

        return result, diagnostics