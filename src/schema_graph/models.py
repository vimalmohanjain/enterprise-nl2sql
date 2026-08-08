from __future__ import annotations
from dataclasses import dataclass, field



@dataclass(slots=True)
class Column:
    name: str
    data_type: str

    nullable: bool = True
    default: str | None = None

    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_unique: bool = False


@dataclass(slots=True)
class ForeignKey:
    """
        Represents one FOREIGN KEY constraint.
        Supports composite keys.
    """
    source_columns: list[str]
    target_table: str
    target_columns: list[str]


@dataclass(slots=True)
class Table:
    """Represents a database table."""

    name: str
    columns: list[Column] = field(default_factory=list)
    foreign_keys: list[ForeignKey] = field(default_factory=list)

    def get_column(self, column_name: str) -> Column | None:
        """Return a column by name."""
        for column in self.columns:
            if column.name == column_name:
                return column
        return None

    def add_column(self, column: Column) -> None:
        """Add a column to the table."""
        self.columns.append(column)

    def add_foreign_key(self, foreign_key: ForeignKey) -> None:
        """Add a foreign key relationship."""
        self.foreign_keys.append(foreign_key)

@dataclass(slots=True)
class DatabaseSchema:
    """Represents an entire database schema."""
    tables: dict[str, Table] = field(default_factory=dict)

    def add_table(self, table: Table) -> None:
        self.tables[table.name] = table

    def get_table(self, table_name: str) -> Table | None:
        return self.tables.get(table_name)

    def __iter__(self):
        return iter(self.tables.values())

    @property
    def relationships(self) -> list[ForeignKey]:
        """Return all foreign key relationships."""
        return [
            fk
            for table in self.tables.values()
            for fk in table.foreign_keys
        ]

@dataclass(slots=True)
class RetrievalResult:
    """Represents the result of a schema retrieval operation."""
    tables: set[str] = field(default_factory=set)
    relationships: list[ForeignKey] = field(default_factory=list)