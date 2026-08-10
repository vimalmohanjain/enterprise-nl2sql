from pathlib import Path

from src.schema_graph.bird_loader import BirdDatasetLoader
from src.schema_graph.context_builder import ContextBuilder
from src.schema_graph.prompt_builder import PromptBuilder
from src.schema_graph.graph_builder import GraphBuilder
from .bird_evaluation import BirdEvaluationExample


class BirdPromptBuilder:
    """Build schema-aware prompts for BIRD evaluation examples."""

    def __init__(
        self,
        *,
        tables_file: str | Path,
        retriever=None,
    ):
        self.tables_file = Path(tables_file)

        self.loader = BirdDatasetLoader()
        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()
        self.retriever = retriever

        self._schema_cache = {}

    def build(
        self,
        example: BirdEvaluationExample,
    ) -> str:
        schema = self._get_schema(example.db_id)

        if self.retriever is None:
            context = self.context_builder.build_full(schema)
        else:
            graph = GraphBuilder().build(schema)

            retrieval = self.retriever.retrieve(
                question=example.question,
                schema=schema,
                graph=graph,
            )

            context = self.context_builder.build(
                retrieval,
                schema,
            )

        return self.prompt_builder.build(
            question=example.question,
            context=context,
        )

    def _get_schema(self, db_id: str):
        if db_id not in self._schema_cache:
            bird_schema = self.loader.load_schema(
                self.tables_file,
                db_id=db_id,
            )

            self._schema_cache[db_id] = (
                self.loader.convert_schema(bird_schema)
            )

        return self._schema_cache[db_id]