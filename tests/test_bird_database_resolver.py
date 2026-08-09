from pathlib import Path

from training.bird_database import BirdDatabaseResolver


def test_bird_database_resolver_returns_sqlite_path(tmp_path):
    db_root = tmp_path / "train_databases"
    db_dir = db_root / "movie_platform"
    db_dir.mkdir(parents=True)

    sqlite_file = db_dir / "movie_platform.sqlite"
    sqlite_file.write_text("dummy")

    resolver = BirdDatabaseResolver(db_root)

    result = resolver.resolve("movie_platform")

    assert result == sqlite_file

