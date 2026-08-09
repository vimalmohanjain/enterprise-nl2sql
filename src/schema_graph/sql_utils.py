import re


def clean_sql(response: str) -> str:
    sql = response.strip()

    fenced_match = re.search(
        r"```(?:sql)?\s*(.*?)```",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if fenced_match:
        sql = fenced_match.group(1).strip()

    if not sql:
        raise ValueError("LLM returned an empty response")

    return sql