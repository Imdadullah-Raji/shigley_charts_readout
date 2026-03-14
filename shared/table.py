import json
from pathlib import Path


class Table:
    """
    Base class representing a single table from Shigley's.
    Loads from a JSON file, supports full-row display and
    nearest-match lookup by a key column.
    """

    def __init__(self, filepath: str):
        """Load table from a JSON file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Table file not found: {filepath}")

        with open(path) as f:
            data = json.load(f)

        # Metadata
        self.id          = data["id"]
        self.chapter     = data["chapter"]
        self.page        = data["page"]
        self.name        = data["name"]
        self.description = data["description"]
        self.notes       = data.get("notes")        # optional
        self.columns     = data.get("columns", [])
        self.series      = data.get("series")       # present in 11-3, None otherwise
        self.key_column  = data.get("key_column")   # primary lookup column
        self.valid_range = data.get("valid_range")  # [min, max] from table bounds

        # Data
        self.rows = data["rows"]

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def get_all_rows(self) -> list:
        """Return all rows exactly as stored — for rendering the full table."""
        return self.rows

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_row(self, key_column: str, value: float) -> dict:
        """
        Return the single row whose key_column value is nearest to `value`.
        Ties go to the lower value (conservative engineering choice).

        Example:
            table.get_row("Bore (mm)", 37)
            → returns the row for Bore = 35
        """
        if not self.rows:
            raise ValueError("Table has no rows.")

        nearest = min(
            self.rows,
            key=lambda row: abs(self._extract_key(row, key_column) - value)
        )
        return nearest

    def get_nearest_pair(self, key_column: str, value: float) -> tuple[dict, dict]:
        """
        Return the (lower, upper) rows that bracket `value`.
        If value is exactly in the table, both will be the same row.
        If value is below the minimum or above the maximum, both
        will be the boundary row.

        Useful for highlighting bracketing rows in the UI.
        """
        keys = [self._extract_key(row, key_column) for row in self.rows]

        # Exact match
        if value in keys:
            row = self.rows[keys.index(value)]
            return (row, row)

        # Below minimum
        if value < keys[0]:
            return (self.rows[0], self.rows[0])

        # Above maximum
        if value > keys[-1]:
            return (self.rows[-1], self.rows[-1])

        # Find bracketing pair
        for i in range(len(keys) - 1):
            if keys[i] < value < keys[i + 1]:
                return (self.rows[i], self.rows[i + 1])

    def available_values(self, key_column: str) -> list:
        """Return all values present in a given column."""
        return [self._extract_key(row, key_column) for row in self.rows]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_key(self, row: dict, key_column: str) -> float:
        """Extract a numeric value from a row, even if it's nested."""
        if key_column in row:
            return float(row[key_column])
        raise KeyError(f"Column '{key_column}' not found in row: {row}")

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Table(id={self.id!r}, name={self.name!r}, "
            f"chapter={self.chapter}, page={self.page}, "
            f"rows={len(self.rows)})"
        )