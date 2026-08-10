import re


class PlanSQLParser:
    """Extract SQL from a structured plan + SQL model response."""

    def parse(self, text: str) -> str:
        match = re.search(
            r"<sql>\s*(.*?)\s*</sql>",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if match:
            return match.group(1).strip()

        # Fallback for partially malformed generations.
        sql_start = re.search(
            r"<sql>\s*(.*)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if sql_start:
            return sql_start.group(1).strip()

        return text.strip()