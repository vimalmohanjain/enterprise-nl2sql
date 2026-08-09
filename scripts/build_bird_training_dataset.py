from pathlib import Path

from transformers import AutoTokenizer

from src.schema_graph.bird_loader import BirdDatasetLoader
from training.bird_dataset_builder import BirdTrainingDatasetBuilder
from training.jsonl import export_records_jsonl
from training.split import split_dataset


MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"

TRAIN_FILE = Path("data/external/bird/train.json")
TABLES_FILE = Path("data/external/bird/train_tables.json")

OUTPUT_DIR = Path("data/training")
TRAIN_OUTPUT = OUTPUT_DIR / "bird_train.jsonl"
VALIDATION_OUTPUT = OUTPUT_DIR / "bird_validation.jsonl"


def main():
    print("Loading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(MODEL)

    print("Loading BIRD dataset...")

    loader = BirdDatasetLoader()

    examples = loader.load_training_examples(
        train_file=TRAIN_FILE,
        tables_file=TABLES_FILE,
    )

    print(f"BIRD examples: {len(examples)}")

    builder = BirdTrainingDatasetBuilder(
        tokenizer=tokenizer,
        max_length=2048,
    )

    print("Building schema-aware training records...")

    records = builder.build(examples)

    train_records, validation_records = split_dataset(
        records,
        validation_ratio=0.1,
        seed=42,
    )

    export_records_jsonl(
        train_records,
        TRAIN_OUTPUT,
    )

    export_records_jsonl(
        validation_records,
        VALIDATION_OUTPUT,
    )

    print()
    print("=" * 60)
    print("BIRD TRAINING DATASET")
    print("=" * 60)
    print("Total records      :", len(records))
    print("Training records   :", len(train_records))
    print("Validation records :", len(validation_records))
    print("Train file         :", TRAIN_OUTPUT)
    print("Validation file    :", VALIDATION_OUTPUT)


if __name__ == "__main__":
    main()