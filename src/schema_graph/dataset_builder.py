from pathlib import Path

from .dataset import DatasetGenerator
from .models import DatasetExample
from .parser import SchemaParser


class MultiSchemaDatasetBuilder:
    """Build one NL2SQL dataset from multiple SQL schema files."""

    def __init__(self):
        self.parser = SchemaParser()
        self.generator = DatasetGenerator()

    def build(
        self,
        schema_directory: str | Path,
    ) -> list[DatasetExample]:
        schema_directory = Path(schema_directory)

        examples: list[DatasetExample] = []
        seen: set[tuple[str, str]] = set()

        for schema_file in sorted(schema_directory.glob("*.sql")):
            ddl = schema_file.read_text(encoding="utf-8")

            schema = self.parser.parse(ddl)

            generated_examples = self.generator.generate(schema)

            for example in generated_examples:
                key = (example.question, example.sql)

                if key in seen:
                    continue

                seen.add(key)
                examples.append(example)

        return examples