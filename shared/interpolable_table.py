from shared.table import Table


class InterpolableTable(Table):
    """
    Subclass of Table for tables where linear interpolation is meaningful.
    Adds interpolate() on top of the base nearest-match lookup.

    Suitable for: Table 11-1 (load factors), Table 11-2 (ball bearings),
    Table 11-3 (cylindrical roller bearings).

    NOT suitable for: categorical tables (e.g. material selection tables
    where rows are discrete named categories, not numeric progressions).
    """

    def interpolate(self, key_column: str, value: float, target_column: str) -> float:
        """
        Linearly interpolate `target_column` at `value` along `key_column`.

        Returns an exact value if `value` is in the table.
        Returns a boundary value if `value` is out of range (no extrapolation).

        Example:
            table.interpolate("Bore (mm)", 37, "Deep Groove C10 (kN)")
            → interpolated C10 between 35mm and 40mm rows

        Args:
            key_column:    the independent variable column (e.g. "Bore (mm)")
            value:         the query value (e.g. 37.0)
            target_column: the column to interpolate (e.g. "Deep Groove C10 (kN)")

        Returns:
            float: interpolated result, rounded to 4 significant figures
        """
        lower, upper = self.get_nearest_pair(key_column, value)

        x0 = self._extract_key(lower, key_column)
        x1 = self._extract_key(upper, key_column)

        y0 = self._extract_target(lower, target_column)
        y1 = self._extract_target(upper, target_column)

        # Exact match or boundary — no interpolation needed
        if x0 == x1:
            return round(y0, 4)

        # Linear interpolation
        result = y0 + (value - x0) * (y1 - y0) / (x1 - x0)
        return round(result, 4)

    def interpolate_row(self, key_column: str, value: float) -> dict:
        """
        Interpolate ALL numeric columns at once and return as a dict.
        Non-numeric columns (e.g. nested series dicts) are skipped.

        Useful for rendering a full interpolated row in the UI.

        Example:
            table.interpolate_row("Bore (mm)", 37)
            → {"Bore (mm)": 37, "OD (mm)": ..., "C10 (kN)": ..., ...}
        """
        lower, upper = self.get_nearest_pair(key_column, value)

        x0 = self._extract_key(lower, key_column)
        x1 = self._extract_key(upper, key_column)

        result = {key_column: value}

        for col in self.columns:
            if col == key_column:
                continue
            try:
                y0 = self._extract_target(lower, col)
                y1 = self._extract_target(upper, col)
                if x0 == x1:
                    result[col] = round(y0, 4)
                else:
                    result[col] = round(
                        y0 + (value - x0) * (y1 - y0) / (x1 - x0), 4
                    )
            except (KeyError, TypeError):
                # Skip non-numeric or nested columns
                continue

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_target(self, row: dict, target_column: str) -> float:
        """Extract a numeric target value from a row."""
        if target_column in row:
            val = row[target_column]
            if isinstance(val, (int, float)):
                return float(val)
            raise TypeError(
                f"Column '{target_column}' is not numeric: {val!r}"
            )
        raise KeyError(f"Column '{target_column}' not found in row: {row}")

    def __repr__(self) -> str:
        return (
            f"InterpolableTable(id={self.id!r}, name={self.name!r}, "
            f"chapter={self.chapter}, page={self.page}, "
            f"rows={len(self.rows)})"
        )