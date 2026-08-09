from pathlib import Path


class BirdDatabaseResolver:
    """Resolve a BIRD database ID to its SQLite database file."""

    def __init__(self, db_root: str | Path):
        self.db_root = Path(db_root)

    def resolve(self, db_id: str) -> Path:
        database_path = (
            self.db_root
            / db_id
            / f"{db_id}.sqlite"
        )

        if not database_path.is_file():
            raise FileNotFoundError(
                f"BIRD database not found: {database_path}"
            )

        return database_path