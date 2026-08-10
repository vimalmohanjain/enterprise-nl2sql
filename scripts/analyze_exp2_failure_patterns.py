import json
import random
import re
import sqlite3
from collections import Counter
from pathlib import Path


TRAIN_FILE = Path("data/external/bird/train.json")

PREDICTIONS_FILE = Path(
    "data/evaluation/exp2-checkpoint-2122-first50.jsonl"
)

DB_ROOT = Path(
    "data/external/bird/train_databases/train_databases"
)


FEATURE_PATTERNS = {
    "JOIN": r"\bJOIN\b",
    "COUNT": r"\bCOUNT\s*\(",
    "SUM": r"\bSUM\s*\(",
    "AVG": r"\bAVG\s*\(",
    "MIN": r"\bMIN\s*\(",
    "MAX": r"\bMAX\s*\(",
    "DISTINCT": r"\bDISTINCT\b",
    "GROUP_BY": r"\bGROUP\s+BY\b",
    "HAVING": r"\bHAVING\b",
    "ORDER_BY": r"\bORDER\s+BY\b",
    "LIMIT": r"\bLIMIT\b",
    "CASE": r"\bCASE\b",
    "OR": r"\bOR\b",
    "AND": r"\bAND\b",
    "LIKE": r"\bLIKE\b",
    "BETWEEN": r"\bBETWEEN\b",
    "IN": r"\bIN\s*\(",
    "UNION": r"\bUNION\b",
    "EXCEPT": r"\bEXCEPT\b",
    "INTERSECT": r"\bINTERSECT\b",
}


def features(sql: str) -> set[str]:
    found = {
        name
        for name, pattern in FEATURE_PATTERNS.items()
        if re.search(
            pattern,
            sql,
            flags=re.IGNORECASE,
        )
    }

    select_count = len(
        re.findall(
            r"\bSELECT\b",
            sql,
            flags=re.IGNORECASE,
        )
    )

    if select_count > 1:
        found.add("SUBQUERY")

    return found


def extract_tables(sql: str) -> set[str]:
    return {
        table.lower()
        for table in re.findall(
            r"\b(?:FROM|JOIN)\s+"
            r'[`"\[]?([A-Za-z_][A-Za-z0-9_]*)',
            sql,
            flags=re.IGNORECASE,
        )
    }


def execute(connection, sql):
    try:
        rows = connection.execute(sql).fetchall()
        return rows, None
    except Exception as exc:
        return None, str(exc)


def main():
    with TRAIN_FILE.open(
        "r",
        encoding="utf-8",
    ) as f:
        records = json.load(f)

    shuffled = list(records)
    random.Random(42).shuffle(shuffled)

    validation_size = int(
        len(shuffled) * 0.1
    )

    validation = shuffled[:validation_size]

    with PREDICTIONS_FILE.open(
        "r",
        encoding="utf-8",
    ) as f:
        predictions = [
            json.loads(line)
            for line in f
            if line.strip()
        ]

    failures = []

    missing_feature_counts = Counter()
    extra_feature_counts = Counter()
    missing_table_counts = Counter()
    extra_table_counts = Counter()

    invalid_predictions = 0
    gold_failures = 0

    for i, prediction in enumerate(predictions):
        record = validation[i]

        db_id = record["db_id"]

        db_path = (
            DB_ROOT
            / db_id
            / f"{db_id}.sqlite"
        )

        gold_sql = prediction["expected_sql"]
        predicted_sql = prediction["predicted_sql"]

        with sqlite3.connect(db_path) as connection:
            gold_rows, gold_error = execute(
                connection,
                gold_sql,
            )

            if gold_error:
                gold_failures += 1
                continue

            predicted_rows, predicted_error = execute(
                connection,
                predicted_sql,
            )

        if (
            predicted_error is None
            and predicted_rows == gold_rows
        ):
            continue

        if predicted_error:
            invalid_predictions += 1

        gold_features = features(gold_sql)
        predicted_features = features(predicted_sql)

        missing_features = (
            gold_features - predicted_features
        )

        extra_features = (
            predicted_features - gold_features
        )

        gold_tables = extract_tables(gold_sql)
        predicted_tables = extract_tables(
            predicted_sql
        )

        missing_tables = (
            gold_tables - predicted_tables
        )

        extra_tables = (
            predicted_tables - gold_tables
        )

        missing_feature_counts.update(
            missing_features
        )

        extra_feature_counts.update(
            extra_features
        )

        missing_table_counts.update(
            missing_tables
        )

        extra_table_counts.update(
            extra_tables
        )

        failures.append(
            {
                "number": i + 1,
                "db_id": db_id,
                "question": prediction["question"],
                "gold": gold_sql,
                "predicted": predicted_sql,
                "missing_features": sorted(
                    missing_features
                ),
                "extra_features": sorted(
                    extra_features
                ),
                "missing_tables": sorted(
                    missing_tables
                ),
                "extra_tables": sorted(
                    extra_tables
                ),
                "error": predicted_error,
            }
        )

    print("=" * 88)
    print("EXPERIMENT 2 — FAILURE PATTERN ANALYSIS")
    print("=" * 88)

    print(f"Prediction failures : {len(failures)}")
    print(f"Invalid predictions : {invalid_predictions}")
    print(f"Gold SQL failures   : {gold_failures}")

    print()
    print("MISSING SQL FEATURES")
    print("-" * 88)

    for name, count in (
        missing_feature_counts.most_common()
    ):
        print(f"{name:20} {count}")

    print()
    print("EXTRA SQL FEATURES")
    print("-" * 88)

    for name, count in (
        extra_feature_counts.most_common()
    ):
        print(f"{name:20} {count}")

    print()
    print("MISSING GOLD TABLES")
    print("-" * 88)

    for name, count in (
        missing_table_counts.most_common()
    ):
        print(f"{name:30} {count}")

    print()
    print("EXTRA PREDICTED TABLES")
    print("-" * 88)

    for name, count in (
        extra_table_counts.most_common()
    ):
        print(f"{name:30} {count}")

    print()
    print("=" * 88)
    print("INDIVIDUAL FAILURES")
    print("=" * 88)

    for item in failures:
        print()
        print(
            f'#{item["number"]} | '
            f'{item["db_id"]}'
        )

        print(f'Q: {item["question"]}')

        print(
            "Missing features:",
            item["missing_features"] or "-",
        )

        print(
            "Extra features:",
            item["extra_features"] or "-",
        )

        print(
            "Missing tables:",
            item["missing_tables"] or "-",
        )

        print(
            "Extra tables:",
            item["extra_tables"] or "-",
        )

        if item["error"]:
            print(
                "Execution error:",
                item["error"],
            )

        print("GOLD:")
        print(item["gold"])

        print("PRED:")
        print(item["predicted"])

        print("-" * 88)


if __name__ == "__main__":
    main()