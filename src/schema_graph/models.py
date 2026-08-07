from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Column:
    """Represents a database column."""

    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False


@dataclass(slots=True)
class ForeignKey:
    """Represents a foreign key relationship."""

    column: str
    referenced_table: str
    referenced_column: str


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


@dataclass(slots=True)
class SchemaMetadata:
    """Represents an entire database schema."""

    tables: dict[str, Table] = field(default_factory=dict)

    def add_table(self, table: Table) -> None:
        self.tables[table.name] = table

    def get_table(self, table_name: str) -> Table | None:
        return self.tables.get(table_name)

    @property
    def relationships(self) -> list[ForeignKey]:
        """Return all foreign key relationships."""
        relations = []
        for table in self.tables.values():
            relations.extend(table.foreign_keys)
        return relations