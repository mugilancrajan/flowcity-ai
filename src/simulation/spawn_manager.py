import random

from src.config import TIME_PERIODS, SPAWN_RATES, SPAWN_ZONE_WEIGHTS, TICKS_PER_DAY, TICKS_PER_SIMULATED_MINUTE
from src.world.tile import TileType
from src.graph.road_network import RoadNetwork
from src.vehicle.vehicle_spawner import VehicleSpawner
from src.vehicle.vehicle import VehicleState
from src.exceptions import NoPathError


class SpawnManager:
    def __init__(self, world, road_network, vehicle_spawner):
        self._road_network = road_network
        self._vehicle_spawner = vehicle_spawner
        self._residential_tiles = world.get_tiles_by_type(TileType.residential)
        self._commercial_tiles = world.get_tiles_by_type(TileType.commercial)
        self._workplace_tiles = world.get_tiles_by_type(TileType.workplace)
        self._ticks_since_last_spawn = 0
        self._spawn_accumulator = 0.0

    def _get_current_period(self, tick):
        day_tick = tick % TICKS_PER_DAY
        for period, bounds in TIME_PERIODS.items():
            if bounds["start_tick"] <= day_tick <= bounds["end_tick"]:
                return period
        return "night"

    def _should_spawn(self, tick, period):
        rate = SPAWN_RATES[period]
        if rate == 0:
            return False
        self._spawn_accumulator += rate / TICKS_PER_SIMULATED_MINUTE
        if self._spawn_accumulator >= 1.0:
            self._spawn_accumulator -= 1.0
            return True
        return False

    def _get_zone_tiles(self, zone_type_string):
        if zone_type_string == "residential":
            return self._residential_tiles
        if zone_type_string == "commercial":
            return self._commercial_tiles
        if zone_type_string == "workplace":
            return self._workplace_tiles
        return []

    def get_spawn(self, tick, next_vehicle_id):
        period = self._get_current_period(tick)
        if not self._should_spawn(tick, period):
            self._ticks_since_last_spawn += 1
            return None

        weights_dict = SPAWN_ZONE_WEIGHTS[period]
        pairs = list(weights_dict.keys())
        weights = list(weights_dict.values())
        origin_zone, dest_zone = random.choices(pairs, weights=weights, k=1)[0]

        origin_tiles = self._get_zone_tiles(origin_zone)
        dest_tiles = self._get_zone_tiles(dest_zone)

        if not origin_tiles or not dest_tiles:
            return None

        origin_tile = random.choice(origin_tiles)
        dest_tile = random.choice(dest_tiles)

        if origin_tile is dest_tile:
            return None

        try:
            path = self._road_network.get_path(origin_tile.position, dest_tile.position)
        except NoPathError:
            return None

        vehicle = self._vehicle_spawner.create(
            next_vehicle_id, origin_tile.position, dest_tile.position, spawn_tick=tick
        )
        vehicle.path = path
        vehicle.state = VehicleState.driving
        self._ticks_since_last_spawn = 0
        return vehicle

    def update_world(self, world):
        self._residential_tiles = world.get_tiles_by_type(TileType.residential)
        self._commercial_tiles = world.get_tiles_by_type(TileType.commercial)
        self._workplace_tiles = world.get_tiles_by_type(TileType.workplace)
