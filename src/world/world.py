from __future__ import annotations
import json
from pathlib import Path
from src.world.tile import Tile, TileType, TrafficControl, _DEFAULT_SPEED_LIMIT

class World:
    def __init__(self, cols: int, rows: int) -> None:
        if cols <= 0 or rows <= 0:
            raise ValueError(f"World dimensions must be positive, got cols={cols}, rows={rows}")
        self._cols = cols
        self._rows = rows
        self._grid: list[list[Tile]] = [
            [Tile(TileType.empty, (col, row)) for col in range(cols)]
            for row in range(rows)
        ]

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def rows(self) -> int:
        return self._rows

    def _check_bounds(self, col: int, row: int) -> None:
        if col < 0 or col >= self._cols or row < 0 or row >= self._rows:
            raise IndexError(
                f"Position ({col}, {row}) is out of bounds for World({self._cols}, {self._rows})"
            )

    def get_tile(self, col: int, row: int) -> Tile:
        self._check_bounds(col, row)
        return self._grid[row][col]

    def set_tile(
            self,
            col: int,
            row: int,
            tile_type: TileType | None = None,
            traffic_control: TrafficControl | None = None,
            speed_limit: int | None = None,
    ) -> None:
        self._check_bounds(col, row)
        tile = self._grid[row][col]
        if tile_type is not None:
            tile.tile_type = tile_type
            # Apply default speed limit for new type only if not explicitly set
            if speed_limit is None:
                tile.speed_limit = _DEFAULT_SPEED_LIMIT[tile_type]
        if traffic_control is not None:
            tile.traffic_control = traffic_control
        if speed_limit is not None:
            tile.speed_limit = speed_limit

    def get_neighbors(self, col: int, row: int) -> list[Tile]:
        self._check_bounds(col, row)
        neighbors = []
        for dc, dr in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nc, nr = col + dc, row + dr
            if 0 <= nc < self._cols and 0 <= nr < self._rows:
                neighbors.append(self._grid[nr][nc])
        return neighbors

    def get_tiles_by_type(self, tile_type: TileType) -> list[Tile]:
        return [
            self._grid[row][col]
            for row in range(self._rows)
            for col in range(self._cols)
            if self._grid[row][col].tile_type == tile_type
        ]

    def to_dict(self) -> dict:
        return {
            "cols": self._cols,
            "rows": self._rows,
            "tiles": [
                self._grid[row][col].to_dict()
                for row in range(self._rows)
                for col in range(self._cols)
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> World:
        for key in ("cols", "rows", "tiles"):
            if key not in data:
                raise ValueError(f"Missing required key: '{key}'")
        world = cls(data["cols"], data["rows"])
        for tile_data in data["tiles"]:
            tile = Tile.from_dict(tile_data)
            col, row = tile.position
            world._grid[row][col] = tile
        return world

    def save(self, filepath: str | Path) -> None:
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def load(cls, filepath: str | Path) -> World:
        with open(filepath) as f:
            data = json.load(f)
        return cls.from_dict(data)
