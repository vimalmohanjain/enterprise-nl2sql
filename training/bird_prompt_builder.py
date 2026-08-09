from pathlib import Path

from src.schema_graph.bird_loader import BirdDatasetLoader
from src.schema_graph.context_builder import ContextBuilder
from src.schema_graph.prompt_builder import PromptBuilder

from .bird_evaluation import BirdEvaluationExample


class BirdPromptBuilder:
    """Build schema-aware prompts for BIRD evaluation examples."""

    def __init__(
        self,
        *,
        tables_file: str | Path,
    ):
        self.tables_file = Path(tables_file)

        self.loader = BirdDatasetLoader()
        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()

        self._schema_cache = {}

    def build(
        self,
        example: BirdEvaluationExample,
    ) -> str:
        schema = self._get_schema(example.db_id)

        context = self.context_builder.build_full(schema)

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