from __future__ import annotations

import numpy as np


class SentenceTransformerTableRanker:
    """Rank schema tables by semantic similarity to a question."""

    def __init__(self, model):
        self.model = model

    def rank(
        self,
        question: str,
        schema,
    ) -> list[str]:
        tables = list(schema)

        if not tables:
            return []

        descriptions = [
            self._describe_table(table)
            for table in tables
        ]

        question_embedding = self.model.encode(
            [question],
            normalize_embeddings=True,
        )[0]

        table_embeddings = self.model.encode(
            descriptions,
            normalize_embeddings=True,
        )

        scores = (
            table_embeddings
            @ question_embedding
        )

        ranked_indices = np.argsort(scores)[::-1]

        return [
            tables[index].name
            for index in ranked_indices
        ]

    def _describe_table(self, table) -> str:
        columns = ", ".join(
            column.name
            for column in table.columns
        )

        return (
            f"Table: {table.name}. "
            f"Columns: {columns}."
        )