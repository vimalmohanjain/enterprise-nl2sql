from dataclasses import dataclass, field

@dataclass(slots=True)
class ForeignKey:
    """
    Represents a foreign key relationship from this table to another table.
    """

    source_columns: list[str] = field(default_factory=list)

    target_table: str = ""

    target_columns: list[str] = field(default_factory=list)