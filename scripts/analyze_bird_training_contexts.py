from pathlib import Path

from transformers import AutoTokenizer

from src.schema_graph.bird_loader import BirdDatasetLoader
from src.schema_graph.context_builder import ContextBuilder
from src.schema_graph.models import DatasetExample
from src.schema_graph.prompt_builder import PromptBuilder
from training.formatter import TrainingFormatter
from training.schema_pruner import TrainingSchemaPruner


MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"

TRAIN_FILE = Path("data/external/bird/train.json")
TABLES_FILE = Path("data/external/bird/train_tables.json")

MAX_LENGTH = 2048


def main():
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL)

    print("Loading BIRD dataset...")
    loader = BirdDatasetLoader()

    examples = loader.load_training_examples(
        train_file=TRAIN_FILE,
        tables_file=TABLES_FILE,
    )

    context_builder = ContextBuilder()
    prompt_builder = PromptBuilder()
    formatter = TrainingFormatter()
    pruner = TrainingSchemaPruner()

    total = len(examples)
    full_schema_fits = 0
    requires_pruning = 0

    full_token_counts = []
    pruned_token_counts = []

    full_table_counts = []
    pruned_table_counts = []

    largest = []

    for index, example in enumerate(examples):
        full_context = context_builder.build_full(
            example.schema
        )

        full_schema_text = (
            prompt_builder.build_schema_context(
                full_context
            )
        )

        dataset_example = DatasetExample(
            question=example.question,
            sql=example.sql,
        )

        full_record = formatter.format(
            dataset_example,
            schema_context=full_schema_text,
        )

        full_tokens = len(
            tokenizer.encode(
                full_record["text"],
                add_special_tokens=True,
            )
        )

        full_tables = len(example.schema.tables)

        full_token_counts.append(full_tokens)
        full_table_counts.append(full_tables)

        if full_tokens <= MAX_LENGTH:
            full_schema_fits += 1
            continue

        requires_pruning += 1

        pruned_schema = pruner.prune(
            schema=example.schema,
            gold_sql=example.sql,
        )

        pruned_context = context_builder.build_full(
            pruned_schema
        )

        pruned_schema_text = (
            prompt_builder.build_schema_context(
                pruned_context
            )
        )

        pruned_record = formatter.format(
            dataset_example,
            schema_context=pruned_schema_text,
        )

        pruned_tokens = len(
            tokenizer.encode(
                pruned_record["text"],
                add_special_tokens=True,
            )
        )

        pruned_tables = len(pruned_schema.tables)

        pruned_token_counts.append(pruned_tokens)
        pruned_table_counts.append(pruned_tables)

        largest.append(
            (
                full_tokens,
                pruned_tokens,
                full_tables,
                pruned_tables,
                example.db_id,
                index,
            )
        )

    print()
    print("=" * 72)
    print("BIRD TRAINING CONTEXT ANALYSIS")
    print("=" * 72)

    print(f"Total examples          : {total}")
    print(
        f"Full schema fits        : "
        f"{full_schema_fits} "
        f"({full_schema_fits / total:.2%})"
    )
    print(
        f"Requires gold pruning   : "
        f"{requires_pruning} "
        f"({requires_pruning / total:.2%})"
    )

    print()
    print(
        f"Average full tokens     : "
        f"{sum(full_token_counts) / total:.1f}"
    )
    print(
        f"Maximum full tokens     : "
        f"{max(full_token_counts)}"
    )
    print(
        f"Average full tables     : "
        f"{sum(full_table_counts) / total:.2f}"
    )

    if pruned_token_counts:
        print()
        print("PRUNED EXAMPLES")
        print(
            f"Average pruned tokens   : "
            f"{sum(pruned_token_counts) / len(pruned_token_counts):.1f}"
        )
        print(
            f"Maximum pruned tokens   : "
            f"{max(pruned_token_counts)}"
        )
        print(
            f"Average pruned tables   : "
            f"{sum(pruned_table_counts) / len(pruned_table_counts):.2f}"
        )

    print()
    print("TOP 20 LARGEST FULL-SCHEMA EXAMPLES")
    print("-" * 72)

    for (
        full_tokens,
        pruned_tokens,
        full_tables,
        pruned_tables,
        db_id,
        index,
    ) in sorted(
        largest,
        reverse=True,
    )[:20]:
        print(
            f"{index:5} | "
            f"{db_id:32} | "
            f"tokens {full_tokens:5} -> {pruned_tokens:5} | "
            f"tables {full_tables:3} -> {pruned_tables:3}"
        )


if __name__ == "__main__":
    main()