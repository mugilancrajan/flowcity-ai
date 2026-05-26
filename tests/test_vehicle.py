import pytest
from src.vehicle.vehicle import Vehicle, VehicleArchetype, VehicleState


def make_vehicle(**kwargs):
    defaults = dict(
        id=1,
        origin=(0, 0),
        destination=(5, 5),
        archetype=VehicleArchetype.normal,
        speed_multiplier=1.0,
        following_distance=1.5,
        spawn_tick=0,
    )
    defaults.update(kwargs)
    return Vehicle(**defaults)


# Construction — identity

def test_id_returns_passed_value():
    v = make_vehicle(id=42)
    assert v.id == 42


def test_origin_returns_passed_value():
    v = make_vehicle(origin=(2, 3))
    assert v.origin == (2, 3)


def test_destination_returns_passed_value():
    v = make_vehicle(destination=(7, 5))
    assert v.destination == (7, 5)


def test_archetype_returns_passed_value():
    v = make_vehicle(archetype=VehicleArchetype.normal)
    assert v.archetype == VehicleArchetype.normal


# Construction — personality

def test_speed_multiplier_returns_passed_value():
    v = make_vehicle(speed_multiplier=1.05)
    assert v.speed_multiplier == 1.05


def test_following_distance_returns_passed_value():
    v = make_vehicle(following_distance=1.5)
    assert v.following_distance == 1.5


# Construction — initial state

def test_initial_state_is_spawning():
    v = make_vehicle()
    assert v.state == VehicleState.spawning


def test_initial_path_is_empty_list():
    v = make_vehicle()
    assert v.path == []


def test_initial_path_index_is_zero():
    v = make_vehicle()
    assert v.path_index == 0


def test_initial_current_speed_is_zero():
    v = make_vehicle()
    assert v.current_speed == 0.0


def test_initial_desired_speed_is_zero():
    v = make_vehicle()
    assert v.desired_speed == 0.0


# Construction — position

def test_position_is_float_version_of_origin():
    v = make_vehicle(origin=(3, 2))
    assert v.position == (3.0, 2.0)


def test_position_values_are_floats():
    v = make_vehicle(origin=(3, 2))
    assert isinstance(v.position[0], float)


# Mutation — settable properties

def test_set_path():
    v = make_vehicle()
    v.path = [(0, 0), (1, 0), (2, 0)]
    assert v.path == [(0, 0), (1, 0), (2, 0)]


def test_set_path_index():
    v = make_vehicle()
    v.path_index = 2
    assert v.path_index == 2


def test_set_position():
    v = make_vehicle()
    v.position = (1.5, 2.0)
    assert v.position == (1.5, 2.0)


def test_set_current_speed():
    v = make_vehicle()
    v.current_speed = 2.5
    assert v.current_speed == 2.5


def test_set_desired_speed():
    v = make_vehicle()
    v.desired_speed = 3.0
    assert v.desired_speed == 3.0


def test_set_state():
    v = make_vehicle()
    v.state = VehicleState.driving
    assert v.state == VehicleState.driving


# Mutation — read-only properties

def test_set_id_raises():
    v = make_vehicle()
    with pytest.raises(AttributeError):
        v.id = 99


def test_set_origin_raises():
    v = make_vehicle()
    with pytest.raises(AttributeError):
        v.origin = (9, 9)


def test_set_destination_raises():
    v = make_vehicle()
    with pytest.raises(AttributeError):
        v.destination = (9, 9)


def test_set_archetype_raises():
    v = make_vehicle()
    with pytest.raises(AttributeError):
        v.archetype = VehicleArchetype.reckless


def test_set_speed_multiplier_raises():
    v = make_vehicle()
    with pytest.raises(AttributeError):
        v.speed_multiplier = 2.0


def test_set_following_distance_raises():
    v = make_vehicle()
    with pytest.raises(AttributeError):
        v.following_distance = 9.9


def test_spawn_tick_returns_passed_value():
    v = make_vehicle(spawn_tick=42)
    assert v.spawn_tick == 42


def test_set_spawn_tick_raises():
    v = make_vehicle()
    with pytest.raises(AttributeError):
        v.spawn_tick = 99
