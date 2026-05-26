import pytest

from src.world.world import World
from src.world.tile import TileType
from src.vehicle.vehicle import Vehicle, VehicleState
from src.simulation.simulation_engine import SimulationEngine
from src.config import (
    DEFAULT_SPEED, SPEED_SLOW, SPEED_NORMAL, SPEED_FAST, SPEED_ULTRA,
    METRICS_SNAPSHOT_INTERVAL, TICKS_PER_DAY,
)


def make_engine():
    w = World(5, 1)
    w.set_tile(0, 0, tile_type=TileType.residential, speed_limit=1)
    w.set_tile(1, 0, tile_type=TileType.road,        speed_limit=3)
    w.set_tile(2, 0, tile_type=TileType.road,        speed_limit=3)
    w.set_tile(3, 0, tile_type=TileType.road,        speed_limit=3)
    w.set_tile(4, 0, tile_type=TileType.workplace,   speed_limit=2)
    return SimulationEngine(w)


def step_until_spawn(engine, max_steps=200):
    for _ in range(max_steps):
        engine.step()
        if engine.total_spawned > 0:
            return True
    return False


# ------------------------------------------------------------------
# Construction
# ------------------------------------------------------------------

def test_construction_no_error():
    make_engine()


def test_initial_tick_is_zero():
    assert make_engine().tick == 0


def test_initial_running_is_false():
    assert make_engine().running is False


def test_initial_active_vehicles_empty():
    assert make_engine().active_vehicles == []


def test_initial_speed_is_default():
    assert make_engine().speed == DEFAULT_SPEED


def test_initial_total_trips_completed_is_zero():
    assert make_engine().total_trips_completed == 0


def test_initial_total_spawned_is_zero():
    assert make_engine().total_spawned == 0


# ------------------------------------------------------------------
# start / pause / resume / reset
# ------------------------------------------------------------------

def test_start_sets_running_true():
    eng = make_engine()
    eng.start()
    assert eng.running is True


def test_start_resets_tick_to_zero():
    eng = make_engine()
    eng.start()
    assert eng.tick == 0


def test_pause_sets_running_false():
    eng = make_engine()
    eng.start()
    eng.pause()
    assert eng.running is False


def test_resume_sets_running_true():
    eng = make_engine()
    eng.start()
    eng.pause()
    eng.resume()
    assert eng.running is True


def test_start_after_steps_resets_tick():
    eng = make_engine()
    eng.start()
    for _ in range(10):
        eng.step()
    eng.start()
    assert eng.tick == 0


def test_reset_sets_running_false():
    eng = make_engine()
    eng.start()
    eng.reset()
    assert eng.running is False


def test_reset_sets_tick_to_zero():
    eng = make_engine()
    eng.start()
    for _ in range(5):
        eng.step()
    eng.reset()
    assert eng.tick == 0


def test_reset_clears_active_vehicles():
    eng = make_engine()
    eng.start()
    eng._tick = 3600
    step_until_spawn(eng, max_steps=50)
    eng.reset()
    assert eng.active_vehicles == []


def test_reset_total_trips_completed_is_zero():
    eng = make_engine()
    eng.start()
    eng.reset()
    assert eng.total_trips_completed == 0


# ------------------------------------------------------------------
# set_speed
# ------------------------------------------------------------------

def test_set_speed_fast():
    eng = make_engine()
    eng.set_speed(SPEED_FAST)
    assert eng.speed == SPEED_FAST


def test_set_speed_slow():
    eng = make_engine()
    eng.set_speed(SPEED_SLOW)
    assert eng.speed == SPEED_SLOW


def test_set_speed_invalid_raises():
    with pytest.raises(ValueError):
        make_engine().set_speed(99999)


# ------------------------------------------------------------------
# time_of_day
# ------------------------------------------------------------------

@pytest.mark.parametrize("tick,expected", [
    (0,      "12:00 AM"),
    (600,    "01:00 AM"),
    (3600,   "06:00 AM"),
    (7200,   "12:00 PM"),
    (10800,  "06:00 PM"),
])
def test_time_of_day(tick, expected):
    eng = make_engine()
    eng._tick = tick
    assert eng.time_of_day == expected


# ------------------------------------------------------------------
# current_period
# ------------------------------------------------------------------

@pytest.mark.parametrize("tick,expected", [
    (0,    "early_morning"),
    (3600, "morning_rush"),
    (9600, "evening_rush"),
])
def test_current_period(tick, expected):
    eng = make_engine()
    eng._tick = tick
    assert eng.current_period == expected


# ------------------------------------------------------------------
# step() — tick advancement
# ------------------------------------------------------------------

def test_one_step_advances_tick():
    eng = make_engine()
    eng.step()
    assert eng.tick == 1


def test_tick_wraps_after_full_day():
    eng = make_engine()
    for _ in range(TICKS_PER_DAY):
        eng.step()
    assert eng.tick == 0


def test_step_works_when_not_running():
    eng = make_engine()
    assert eng.running is False
    eng.step()
    assert eng.tick == 1


# ------------------------------------------------------------------
# step() — spawning
# ------------------------------------------------------------------

def test_total_spawned_increases_during_morning_rush():
    eng = make_engine()
    eng._tick = 3600
    for _ in range(200):
        eng.step()
    assert eng.total_spawned > 0


def test_active_vehicles_are_vehicle_instances():
    eng = make_engine()
    eng._tick = 3600
    step_until_spawn(eng, max_steps=50)
    assert all(isinstance(v, Vehicle) for v in eng.active_vehicles)


def test_active_vehicles_have_nonempty_paths():
    eng = make_engine()
    eng._tick = 3600
    step_until_spawn(eng, max_steps=50)
    assert all(len(v.path) > 0 for v in eng.active_vehicles)


# ------------------------------------------------------------------
# step() — movement
# ------------------------------------------------------------------

def test_vehicle_position_changes_from_origin():
    eng = make_engine()
    eng._tick = 3600
    step_until_spawn(eng, max_steps=50)
    if not eng.active_vehicles:
        pytest.skip("No vehicle spawned")
    v = eng.active_vehicles[0]
    origin = v.origin
    # Step a few more times to ensure movement
    for _ in range(5):
        eng.step()
    assert v.position != (float(origin[0]), float(origin[1]))


def test_vehicle_position_is_float_tuple():
    eng = make_engine()
    eng._tick = 3600
    step_until_spawn(eng, max_steps=50)
    if not eng.active_vehicles:
        pytest.skip("No vehicle spawned")
    for v in eng.active_vehicles:
        assert isinstance(v.position[0], float)
        assert isinstance(v.position[1], float)


def test_path_index_never_exceeds_path_length():
    eng = make_engine()
    eng._tick = 3600
    for _ in range(500):
        eng.step()
        for v in eng.active_vehicles:
            assert v.path_index <= len(v.path) - 1


# ------------------------------------------------------------------
# step() — arrival
# ------------------------------------------------------------------

def test_total_trips_completed_increases_on_arrival():
    eng = make_engine()
    eng._tick = 3600
    for _ in range(1000):
        eng.step()
    assert eng.total_trips_completed > 0


def test_arrived_vehicles_removed_from_active():
    eng = make_engine()
    eng._tick = 3600
    for _ in range(1000):
        eng.step()
    for v in eng.active_vehicles:
        assert v.state != VehicleState.arrived


# ------------------------------------------------------------------
# step() — tile live data
# ------------------------------------------------------------------

def test_tile_car_count_nonzero_with_driving_vehicles():
    eng = make_engine()
    eng._tick = 3600
    step_until_spawn(eng, max_steps=50)
    # Step once more to let Phase 5 update tile counts
    eng.step()
    world = eng._world
    counts = [
        world.get_tile(col, row).car_count
        for row in range(world.rows)
        for col in range(world.cols)
    ]
    assert any(c > 0 for c in counts)


def test_tile_car_count_zero_after_all_vehicles_arrive():
    eng = make_engine()
    eng._tick = 3600
    # Spawn a small batch of vehicles
    for _ in range(20):
        eng.step()
    # Remove zone tiles so no new vehicles spawn
    world = eng._world
    world.set_tile(0, 0, tile_type=TileType.road, speed_limit=1)
    world.set_tile(4, 0, tile_type=TileType.road, speed_limit=2)
    eng._spawn_manager.update_world(world)
    # Wait long enough for all in-flight vehicles to arrive
    for _ in range(500):
        if not eng.active_vehicles:
            break
        eng.step()
    if eng.active_vehicles:
        pytest.skip("Vehicles still active after extended wait")
    # One more step flushes Phase 5 tile data with no drivers
    eng.step()
    counts = [
        world.get_tile(col, row).car_count
        for row in range(world.rows)
        for col in range(world.cols)
    ]
    assert all(c == 0 for c in counts)


# ------------------------------------------------------------------
# step() — metrics
# ------------------------------------------------------------------

def test_metrics_snapshot_after_interval_steps():
    eng = make_engine()
    for _ in range(METRICS_SNAPSHOT_INTERVAL):
        eng.step()
    assert len(eng.metrics_snapshots) == 1


def test_metrics_two_snapshots_after_two_intervals():
    eng = make_engine()
    for _ in range(2 * METRICS_SNAPSHOT_INTERVAL):
        eng.step()
    assert len(eng.metrics_snapshots) == 2


def test_snapshot_has_required_keys():
    eng = make_engine()
    for _ in range(METRICS_SNAPSHOT_INTERVAL):
        eng.step()
    snapshot = eng.metrics_snapshots[0]
    required = {
        "tick", "total_trips_completed", "trips_this_interval", "active_vehicles",
        "total_spawned", "average_travel_time", "congestion_index",
        "average_speed_ratio", "city_health_score", "top_congested_tiles",
    }
    assert required == set(snapshot.keys())


def test_city_health_score_in_range():
    eng = make_engine()
    eng._tick = 3600
    for _ in range(METRICS_SNAPSHOT_INTERVAL * 2):
        eng.step()
    for snap in eng.metrics_snapshots:
        assert 0 <= snap["city_health_score"] <= 100


def test_congestion_index_in_range():
    eng = make_engine()
    eng._tick = 3600
    for _ in range(METRICS_SNAPSHOT_INTERVAL * 2):
        eng.step()
    for snap in eng.metrics_snapshots:
        assert 0 <= snap["congestion_index"] <= 100


def test_top_congested_tiles_at_most_five():
    eng = make_engine()
    eng._tick = 3600
    for _ in range(METRICS_SNAPSHOT_INTERVAL * 2):
        eng.step()
    for snap in eng.metrics_snapshots:
        assert len(snap["top_congested_tiles"]) <= 5


# ------------------------------------------------------------------
# reset() — world unchanged
# ------------------------------------------------------------------

def test_reset_leaves_world_tiles_unchanged():
    eng = make_engine()
    world = eng._world
    tile_types_before = [
        world.get_tile(col, row).tile_type
        for row in range(world.rows)
        for col in range(world.cols)
    ]
    eng.start()
    eng._tick = 3600
    for _ in range(500):
        eng.step()
    eng.reset()
    tile_types_after = [
        world.get_tile(col, row).tile_type
        for row in range(world.rows)
        for col in range(world.cols)
    ]
    assert tile_types_before == tile_types_after
