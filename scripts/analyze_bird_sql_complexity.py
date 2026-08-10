import json
import re
from collections import Counter, defaultdict
from pathlib import Path


TRAIN_FILE = Path("data/external/bird/train.json")


FEATURES = {
    "join": r"\bJOIN\b",
    "group_by": r"\bGROUP\s+BY\b",
    "having": r"\bHAVING\b",
    "distinct": r"\bDISTINCT\b",
    "order_by": r"\bORDER\s+BY\b",
    "limit": r"\bLIMIT\b",
    "case": r"\bCASE\b",
    "union": r"\bUNION\b",
    "intersect": r"\bINTERSECT\b",
    "except": r"\bEXCEPT\b",
    "count": r"\bCOUNT\s*\(",
    "sum": r"\bSUM\s*\(",
    "avg": r"\bAVG\s*\(",
    "min": r"\bMIN\s*\(",
    "max": r"\bMAX\s*\(",
}


def has_feature(sql: str, pattern: str) -> bool:
    return (
        re.search(
            pattern,
            sql,
            flags=re.IGNORECASE,
        )
        is not None
    )


def count_selects(sql: str) -> int:
    return len(
        re.findall(
            r"\bSELECT\b",
            sql,
            flags=re.IGNORECASE,
        )
    )


def count_joins(sql: str) -> int:
    return len(
        re.findall(
            r"\bJOIN\b",
            sql,
            flags=re.IGNORECASE,
        )
    )


def count_tables(sql: str) -> int:
    """
    Approximate number of tables referenced by FROM/JOIN.

    This is sufficient for distribution analysis; it is not intended
    to replace a SQL parser.
    """
    tables = re.findall(
        r"\b(?:FROM|JOIN)\s+"
        r'[`"\[]?([A-Za-z_][A-Za-z0-9_]*)',
        sql,
        flags=re.IGNORECASE,
    )

    return len(set(table.lower() for table in tables))


def classify(sql: str) -> dict:
    result = {
        name: has_feature(sql, pattern)
        for name, pattern in FEATURES.items()
    }

    result["aggregate"] = any(
        result[name]
        for name in (
            "count",
            "sum",
            "avg",
            "min",
            "max",
        )
    )

    result["set_operation"] = any(
        result[name]
        for name in (
            "union",
            "intersect",
            "except",
        )
    )

    result["select_count"] = count_selects(sql)
    result["subquery"] = result["select_count"] > 1

    result["join_count"] = count_joins(sql)
    result["table_count"] = count_tables(sql)

    result["multi_table"] = result["table_count"] > 1

    # Useful combined categories.
    result["multi_table_aggregate"] = (
        result["multi_table"]
        and result["aggregate"]
    )

    result["grouped_aggregate"] = (
        result["group_by"]
        and result["aggregate"]
    )

    result["ordered_limit"] = (
        result["order_by"]
        and result["limit"]
    )

    result["complex_composition"] = sum(
        [
            result["multi_table"],
            result["aggregate"],
            result["group_by"],
            result["having"],
            result["subquery"],
            result["set_operation"],
            result["case"],
            result["order_by"],
        ]
    ) >= 3

    return result


def percentage(count: int, total: int) -> str:
    return f"{count / total:.2%}"


def main():
    with TRAIN_FILE.open(
        "r",
        encoding="utf-8",
    ) as f:
        records = json.load(f)

    feature_counts = Counter()
    join_distribution = Counter()
    table_distribution = Counter()
    select_distribution = Counter()

    by_database = defaultdict(Counter)

    for record in records:
        sql = record["SQL"]
        db_id = record["db_id"]

        features = classify(sql)

        for name, value in features.items():
            if isinstance(value, bool) and value:
                feature_counts[name] += 1
                by_database[db_id][name] += 1

        join_distribution[
            features["join_count"]
        ] += 1

        table_distribution[
            features["table_count"]
        ] += 1

        select_distribution[
            features["select_count"]
        ] += 1

    total = len(records)

    print("=" * 76)
    print("BIRD TRAINING SQL COMPLEXITY")
    print("=" * 76)

    print(f"Total examples: {total}")

    print()
    print("CORE FEATURES")
    print("-" * 76)

    feature_order = [
        "multi_table",
        "join",
        "aggregate",
        "multi_table_aggregate",
        "group_by",
        "grouped_aggregate",
        "having",
        "distinct",
        "order_by",
        "limit",
        "ordered_limit",
        "subquery",
        "case",
        "set_operation",
        "union",
        "intersect",
        "except",
        "complex_composition",
    ]

    for name in feature_order:
        count = feature_counts[name]

        print(
            f"{name:24} "
            f"{count:5} / {total} "
            f"({percentage(count, total)})"
        )

    print()
    print("AGGREGATE FUNCTIONS")
    print("-" * 76)

    for name in [
        "count",
        "sum",
        "avg",
        "min",
        "max",
    ]:
        count = feature_counts[name]

        print(
            f"{name:24} "
            f"{count:5} / {total} "
            f"({percentage(count, total)})"
        )

    print()
    print("TABLE COUNT DISTRIBUTION")
    print("-" * 76)

    for count in sorted(table_distribution):
        examples = table_distribution[count]

        print(
            f"{count:2} tables : "
            f"{examples:5} "
            f"({percentage(examples, total)})"
        )

    print()
    print("JOIN COUNT DISTRIBUTION")
    print("-" * 76)

    for count in sorted(join_distribution):
        examples = join_distribution[count]

        print(
            f"{count:2} joins  : "
            f"{examples:5} "
            f"({percentage(examples, total)})"
        )

    print()
    print("SELECT COUNT DISTRIBUTION")
    print("-" * 76)

    for count in sorted(select_distribution):
        examples = select_distribution[count]

        print(
            f"{count:2} SELECTs: "
            f"{examples:5} "
            f"({percentage(examples, total)})"
        )

    print()
    print("TOP DATABASES BY COMPLEX COMPOSITION")
    print("-" * 76)

    ranked = sorted(
        (
            (
                counts["complex_composition"],
                db_id,
            )
            for db_id, counts in by_database.items()
        ),
        reverse=True,
    )

    for count, db_id in ranked[:20]:
        print(
            f"{db_id:35} "
            f"{count:4}"
        )


if __name__ == "__main__":
    main()
    