import json
from pathlib import Path

from shared.table import Table
from shared.interpolable_table import InterpolableTable


class TableRepository:
    """
    Loads and indexes all table JSON files from a data directory.
    Acts as the single source of truth for the Flask app —
    routes ask the repository for tables, never touching files directly.

    Usage:
        repo = TableRepository("data/chapters/ch11")
        table = repo.get("11-1")
        tables = repo.by_chapter(11)
    """

    def __init__(self, data_dir: str):
        """
        Recursively scan data_dir for all JSON files and load them.
        Instantiates InterpolableTable or Table based on the
        'interpolable' flag in each JSON file.
        """
        self._tables: dict[str, Table] = {}
        self._data_dir = Path(data_dir)

        if not self._data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

        self._load_all()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_all(self):
        """Scan directory recursively and load every JSON file found."""
        json_files = sorted(self._data_dir.rglob("*.json"))

        if not json_files:
            raise ValueError(f"No JSON files found in: {self._data_dir}")

        for filepath in json_files:
            try:
                table = self._load_one(filepath)
                if table.id in self._tables:
                    raise ValueError(
                        f"Duplicate table id '{table.id}' found in {filepath}"
                    )
                self._tables[table.id] = table
            except Exception as e:
                print(f"Warning: could not load {filepath.name}: {e}")

        print(f"TableRepository: loaded {len(self._tables)} tables from {self._data_dir}")

    def _load_one(self, filepath: Path) -> Table:
        """Read the JSON, check the interpolable flag, return the right class."""
        with open(filepath) as f:
            data = json.load(f)

        interpolable = data.get("interpolable", False)

        if interpolable:
            return InterpolableTable(str(filepath))
        else:
            return Table(str(filepath))

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self, table_id: str) -> Table:
        """
        Retrieve a table by its id (e.g. '11-1').
        Raises KeyError with helpful message if not found.
        """
        if table_id not in self._tables:
            available = ", ".join(sorted(self._tables.keys()))
            raise KeyError(
                f"Table '{table_id}' not found. Available tables: {available}"
            )
        return self._tables[table_id]

    def all(self) -> list[Table]:
        """Return all loaded tables, sorted by id."""
        return sorted(self._tables.values(), key=lambda t: t.id)

    def by_chapter(self, chapter: int) -> list[Table]:
        """Return all tables belonging to a given chapter."""
        return [t for t in self.all() if t.chapter == chapter]

    def search(self, query: str) -> list[Table]:
        """
        Case-insensitive search across table name and description.
        Returns all tables where query appears in either field.
        """
        query_lower = query.lower()
        return [
            t for t in self.all()
            if query_lower in t.name.lower()
            or query_lower in (t.description or "").lower()
        ]

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def summary(self) -> list[dict]:
        """
        Return a lightweight summary of all tables — useful for
        rendering a table-of-contents page in the UI.
        """
        return [
            {
                "id": t.id,
                "chapter": t.chapter,
                "page": t.page,
                "name": t.name,
                "interpolable": isinstance(t, InterpolableTable),
                "row_count": len(t.rows),
            }
            for t in self.all()
        ]

    def __len__(self) -> int:
        return len(self._tables)

    def __repr__(self) -> str:
        return (
            f"TableRepository(dir={self._data_dir}, "
            f"tables={list(self._tables.keys())})"
        )