import re


class SQLPlanBuilder:
    """Build a compact deterministic plan from gold SQL."""

    def build(self, sql: str) -> str:
        tables = self._extract_tables(sql)
        joins = self._extract_joins(sql)
        filters = self._extract_filters(sql)
        grouping = self._extract_clause(
            sql,
            "GROUP BY",
            stop_keywords=[
                "HAVING",
                "ORDER BY",
                "LIMIT",
                "UNION",
            ],
        )
        having = self._extract_clause(
            sql,
            "HAVING",
            stop_keywords=[
                "ORDER BY",
                "LIMIT",
                "UNION",
            ],
        )
        ordering = self._extract_clause(
            sql,
            "ORDER BY",
            stop_keywords=[
                "LIMIT",
                "UNION",
            ],
        )

        aggregates = self._extract_aggregates(sql)
        limit = self._extract_limit(sql)
        set_operations = self._extract_set_operations(sql)
        subquery_count = max(
            0,
            len(
                re.findall(
                    r"\bSELECT\b",
                    sql,
                    flags=re.IGNORECASE,
                )
            )
            - 1,
        )

        lines = [
            f"TABLES: {self._join_or_none(tables)}",
            f"JOINS: {self._join_or_none(joins)}",
            f"FILTERS: {filters or 'NONE'}",
            f"GROUPING: {grouping or 'NONE'}",
            f"HAVING: {having or 'NONE'}",
            f"AGGREGATES: {self._join_or_none(aggregates)}",
            f"ORDERING: {ordering or 'NONE'}",
            f"LIMIT: {limit or 'NONE'}",
            f"SET_OPERATIONS: {self._join_or_none(set_operations)}",
            f"SUBQUERIES: {subquery_count}",
        ]

        return "\n".join(lines)

    def _extract_tables(
        self,
        sql: str,
    ) -> list[str]:
        tables = re.findall(
            r"\b(?:FROM|JOIN)\s+"
            r'[`"\[]?([A-Za-z_][A-Za-z0-9_-]*)',
            sql,
            flags=re.IGNORECASE,
        )

        return self._dedupe_preserving_order(tables)

    def _extract_joins(
        self,
        sql: str,
    ) -> list[str]:
        return [
            match.strip()
            for match in re.findall(
                r"\bON\s+(.+?)"
                r"(?=\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\b"
                r"|\bWHERE\b"
                r"|\bGROUP\s+BY\b"
                r"|\bHAVING\b"
                r"|\bORDER\s+BY\b"
                r"|\bLIMIT\b"
                r"|\bUNION\b"
                r"|$)",
                sql,
                flags=re.IGNORECASE | re.DOTALL,
            )
        ]

    def _extract_filters(
        self,
        sql: str,
    ) -> str:
        return self._extract_clause(
            sql,
            "WHERE",
            stop_keywords=[
                "GROUP BY",
                "HAVING",
                "ORDER BY",
                "LIMIT",
                "UNION",
            ],
        )

    def _extract_clause(
        self,
        sql: str,
        keyword: str,
        *,
        stop_keywords: list[str],
    ) -> str:
        escaped_keyword = re.escape(keyword).replace(
            r"\ ",
            r"\s+",
        )

        stop_pattern = "|".join(
            re.escape(item).replace(
                r"\ ",
                r"\s+",
            )
            for item in stop_keywords
        )

        pattern = (
            rf"\b{escaped_keyword}\b\s+(.+?)"
            rf"(?=\b(?:{stop_pattern})\b|$)"
        )

        match = re.search(
            pattern,
            sql,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return ""

        return " ".join(
            match.group(1).split()
        )

    def _extract_aggregates(
        self,
        sql: str,
    ) -> list[str]:
        matches = re.findall(
            r"\b(COUNT|SUM|AVG|MIN|MAX)\s*"
            r"\((.*?)\)",
            sql,
            flags=re.IGNORECASE | re.DOTALL,
        )

        aggregates = [
            f"{function.upper()}("
            f"{' '.join(expression.split())})"
            for function, expression in matches
        ]

        return self._dedupe_preserving_order(
            aggregates
        )

    def _extract_limit(
        self,
        sql: str,
    ) -> str:
        match = re.search(
            r"\bLIMIT\s+(\d+)",
            sql,
            flags=re.IGNORECASE,
        )

        return match.group(1) if match else ""

    def _extract_set_operations(
        self,
        sql: str,
    ) -> list[str]:
        return [
            match.upper()
            for match in re.findall(
                r"\b(UNION(?:\s+ALL)?|INTERSECT|EXCEPT)\b",
                sql,
                flags=re.IGNORECASE,
            )
        ]

    def _join_or_none(
        self,
        values: list[str],
    ) -> str:
        return (
            "; ".join(values)
            if values
            else "NONE"
        )

    def _dedupe_preserving_order(
        self,
        values: list[str],
    ) -> list[str]:
        seen = set()
        result = []

        for value in values:
            lowered = value.lower()

            if lowered in seen:
                continue

            seen.add(lowered)
            result.append(value)

        return result