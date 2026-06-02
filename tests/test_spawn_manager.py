import pytest

from src.world.world import World
from src.world.tile import TileType
from src.graph.road_network import RoadNetwork
from src.vehicle.vehicle_spawner import VehicleSpawner
from src.vehicle.vehicle import Vehicle, VehicleState
from src.simulation.spawn_manager import SpawnManager


def make_city_world():
    w = World(5, 1)
    w.set_tile(0, 0, tile_type=TileType.residential)
    w.set_tile(1, 0, tile_type=TileType.road)
    w.set_tile(2, 0, tile_type=TileType.road)
    w.set_tile(3, 0, tile_type=TileType.road)
    w.set_tile(4, 0, tile_type=TileType.workplace)
    return w


def make_spawn_manager(world=None):
    if world is None:
        world = make_city_world()
    rn = RoadNetwork(world)
    vs = VehicleSpawner()
    return SpawnManager(world, rn, vs)


def pump_for_vehicle(sm, start_tick, max_ticks=100):
    for tick in range(start_tick, start_tick + max_ticks):
        v = sm.get_spawn(tick, 1)
        if v is not None:
            return v
    return None


# ------------------------------------------------------------------
# Construction
# ------------------------------------------------------------------

def test_construction_valid_world():
    make_spawn_manager()


def test_construction_empty_world():
    w = World(3, 3)
    rn = RoadNetwork(w)
    vs = VehicleSpawner()
    SpawnManager(w, rn, vs)


# ------------------------------------------------------------------
# Time period detection
# ------------------------------------------------------------------

@pytest.mark.parametrize("tick,expected", [
    (0,       "early_morning"),
    (7200,    "morning_rush"),
    (10800,   "midday"),
    (19200,   "evening_rush"),
    (22800,   "night"),
    (28799,   "night"),
    (28800,   "early_morning"),
])
def test_get_current_period(tick, expected):
    sm = make_spawn_manager()
    assert sm._get_current_period(tick) == expected


# ------------------------------------------------------------------
# Spawn — None cases
# ------------------------------------------------------------------

def test_spawn_no_residential_returns_none():
    w = World(5, 1)
    w.set_tile(0, 0, tile_type=TileType.road)
    w.set_tile(1, 0, tile_type=TileType.road)
    w.set_tile(2, 0, tile_type=TileType.road)
    w.set_tile(3, 0, tile_type=TileType.road)
    w.set_tile(4, 0, tile_type=TileType.workplace)
    sm = make_spawn_manager(w)
    for tick in range(3600, 3650):
        assert sm.get_spawn(tick, 1) is None


def test_spawn_no_workplace_returns_none():
    w = World(5, 1)
    w.set_tile(0, 0, tile_type=TileType.residential)
    w.set_tile(1, 0, tile_type=TileType.road)
    w.set_tile(2, 0, tile_type=TileType.road)
    w.set_tile(3, 0, tile_type=TileType.road)
    w.set_tile(4, 0, tile_type=TileType.road)
    sm = make_spawn_manager(w)
    for tick in range(3600, 3650):
        assert sm.get_spawn(tick, 1) is None


# ------------------------------------------------------------------
# Spawn — valid vehicle
# ------------------------------------------------------------------

def test_spawn_returns_vehicle_on_valid_world():
    sm = make_spawn_manager()
    vehicle = pump_for_vehicle(sm, start_tick=3600)
    assert vehicle is not None


def test_returned_vehicle_origin_is_valid_position():
    world = make_city_world()
    rn = RoadNetwork(world)
    vs = VehicleSpawner()
    sm = SpawnManager(world, rn, vs)
    vehicle = pump_for_vehicle(sm, start_tick=3600)
    assert vehicle is not None
    col, row = vehicle.origin
    tile = world.get_tile(col, row)
    assert tile is not None


def test_returned_vehicle_destination_is_valid_position():
    world = make_city_world()
    rn = RoadNetwork(world)
    vs = VehicleSpawner()
    sm = SpawnManager(world, rn, vs)
    vehicle = pump_for_vehicle(sm, start_tick=3600)
    assert vehicle is not None
    col, row = vehicle.destination
    tile = world.get_tile(col, row)
    assert tile is not None


def test_returned_vehicle_has_nonempty_path():
    sm = make_spawn_manager()
    vehicle = pump_for_vehicle(sm, start_tick=3600)
    assert vehicle is not None
    assert len(vehicle.path) > 0


def test_returned_vehicle_path_first_matches_origin():
    sm = make_spawn_manager()
    vehicle = pump_for_vehicle(sm, start_tick=3600)
    assert vehicle is not None
    assert vehicle.path[0] == vehicle.origin


def test_returned_vehicle_path_last_matches_destination():
    sm = make_spawn_manager()
    vehicle = pump_for_vehicle(sm, start_tick=3600)
    assert vehicle is not None
    assert vehicle.path[-1] == vehicle.destination


def test_returned_vehicle_state_is_driving():
    sm = make_spawn_manager()
    vehicle = pump_for_vehicle(sm, start_tick=3600)
    assert vehicle is not None
    assert vehicle.state == VehicleState.driving


# ------------------------------------------------------------------
# update_world
# ------------------------------------------------------------------

def test_update_world_enables_spawn():
    # Start with a world that has no residential tiles — only road + workplace
    old_world = World(5, 1)
    old_world.set_tile(0, 0, tile_type=TileType.road)
    old_world.set_tile(1, 0, tile_type=TileType.road)
    old_world.set_tile(2, 0, tile_type=TileType.road)
    old_world.set_tile(3, 0, tile_type=TileType.road)
    old_world.set_tile(4, 0, tile_type=TileType.workplace)
    rn = RoadNetwork(old_world)
    vs = VehicleSpawner()
    sm = SpawnManager(old_world, rn, vs)

    # Confirm no vehicle spawns
    for tick in range(3600, 3610):
        assert sm.get_spawn(tick, 1) is None

    # Replace with a world that has residential at position (0,0)
    new_world = make_city_world()
    new_rn = RoadNetwork(new_world)
    sm._road_network = new_rn
    sm.update_world(new_world)

    # Now a vehicle should be spawnable
    vehicle = pump_for_vehicle(sm, start_tick=3610, max_ticks=100)
    assert vehicle is not None
