import copy
import random

from src.vehicle.vehicle import Vehicle, VehicleArchetype


ARCHETYPE_CONFIGS = {
    VehicleArchetype.conservative: {
        "speed_range": (0.75, 0.95),
        "following_range": (1.75, 2.5),
        "weight": 20
    },
    VehicleArchetype.normal: {
        "speed_range": (0.85, 1.15),
        "following_range": (1.0, 2.0),
        "weight": 50
    },
    VehicleArchetype.aggressive: {
        "speed_range": (1.1, 1.35),
        "following_range": (0.5, 1.0),
        "weight": 20
    },
    VehicleArchetype.reckless: {
        "speed_range": (1.3, 1.6),
        "following_range": (0.1, 0.5),
        "weight": 10
    }
}


class VehicleSpawner:
    def __init__(self, speed_overrides=None, weight_overrides=None):
        self._config = copy.deepcopy(ARCHETYPE_CONFIGS)
        if speed_overrides:
            for archetype, speed_range in speed_overrides.items():
                self._config[archetype]["speed_range"] = speed_range
        if weight_overrides:
            for archetype, weight in weight_overrides.items():
                self._config[archetype]["weight"] = weight

    def create(self, id, origin, destination):
        archetypes = list(self._config.keys())
        weights = [self._config[a]["weight"] for a in archetypes]
        archetype = random.choices(archetypes, weights=weights, k=1)[0]
        return self._build(id, origin, destination, archetype)

    def create_with_archetype(self, id, origin, destination, archetype):
        return self._build(id, origin, destination, archetype)

    def _build(self, id, origin, destination, archetype):
        config = self._config[archetype]
        speed_multiplier = random.uniform(*config["speed_range"])
        following_distance = random.uniform(*config["following_range"])
        return Vehicle(id, origin, destination, archetype, speed_multiplier, following_distance)
