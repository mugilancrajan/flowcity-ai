from __future__ import annotations
from enum import Enum, auto


class TileType(Enum):
    empty = auto()
    road = auto()
    highway = auto()
    residential = auto()
    commercial = auto()
    workplace = auto()


class TrafficControl(Enum):
    none = auto()
    stop_sign = auto()
    traffic_light = auto()


_DEFAULT_SPEED_LIMIT: dict[TileType, int] = {
    TileType.empty: 0,
    TileType.road: 3,
    TileType.highway: 6,
    TileType.residential: 1,
    TileType.commercial: 2,
    TileType.workplace: 2,
}


class Tile:
    def __init__(
        self,
        tile_type: TileType,
        position: tuple[int, int],
        traffic_control: TrafficControl = TrafficControl.none,
        speed_limit: int | None = None,
        capacity: int = 0,
    ) -> None:
        self.tile_type = tile_type
        self.position = position
        self.traffic_control = traffic_control
        self.speed_limit = speed_limit if speed_limit is not None else _DEFAULT_SPEED_LIMIT[tile_type]
        self.capacity = capacity

        # Live data — runtime only, not saved
        self.car_count: int = 0
        self.car_speed: float = 0.0

    @property
    def congestion(self) -> float:
        if self.speed_limit == 0:
            return 0.0
        return self.car_speed / self.speed_limit

    def reset_live_data(self) -> None:
        self.car_count = 0
        self.car_speed = 0.0

    def to_dict(self) -> dict:
        return {
            "tile_type": self.tile_type.name,
            "traffic_control": self.traffic_control.name,
            "speed_limit": self.speed_limit,
            "position": list(self.position),
            "capacity": self.capacity,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Tile:
        return cls(
            tile_type=TileType[data["tile_type"]],
            position=tuple(data["position"]),
            traffic_control=TrafficControl[data["traffic_control"]],
            speed_limit=data["speed_limit"],
            capacity=data["capacity"],
        )
