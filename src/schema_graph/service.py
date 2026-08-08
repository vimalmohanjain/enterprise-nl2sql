from .context_builder import ContextBuilder
from .generator import LLMClient, NL2SQLGenerator
from .graph_builder import GraphBuilder
from .models import DatabaseSchema
from .prompt_builder import PromptBuilder
from .retriever import SchemaRetriever


class NL2SQLService:
    """Orchestrate schema retrieval, prompt building, and SQL generation."""

    def __init__(self, client: LLMClient):
        self._retriever = SchemaRetriever()
        self._context_builder = ContextBuilder()
        self._prompt_builder = PromptBuilder()
        self._generator = NL2SQLGenerator(client)

    def generate(
        self,
        question: str,
        schema: DatabaseSchema,
    ) -> str:
        graph = GraphBuilder().build(schema)

        retrieval = self._retriever.retrieve(
            question,
            schema,
            graph,
        )

        context = self._context_builder.build(
            retrieval,
            schema,
        )

        prompt = self._prompt_builder.build(
            question,
            context,
        )

        return self._generator.generate(prompt)