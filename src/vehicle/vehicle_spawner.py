import copy
import random

from src.vehicle.vehicle import Vehicle, VehicleArchetype
from src.config import ARCHETYPE_CONFIGS


class VehicleSpawner:
    def __init__(self, speed_overrides=None, weight_overrides=None):
        self._config = copy.deepcopy(ARCHETYPE_CONFIGS)
        if speed_overrides:
            for archetype, speed_range in speed_overrides.items():
                self._config[archetype]["speed_range"] = speed_range
        if weight_overrides:
            for archetype, weight in weight_overrides.items():
                self._config[archetype]["weight"] = weight

    def create(self, id, origin, destination, spawn_tick):
        archetypes = list(self._config.keys())
        weights = [self._config[a]["weight"] for a in archetypes]
        archetype = random.choices(archetypes, weights=weights, k=1)[0]
        return self._build(id, origin, destination, archetype, spawn_tick)

    def create_with_archetype(self, id, origin, destination, archetype, spawn_tick):
        return self._build(id, origin, destination, archetype, spawn_tick)

    def _build(self, id, origin, destination, archetype, spawn_tick):
        config = self._config[archetype]
        speed_multiplier = random.uniform(*config["speed_range"])
        following_distance = random.uniform(*config["following_range"])
        return Vehicle(id, origin, destination, archetype, speed_multiplier, following_distance, spawn_tick)
