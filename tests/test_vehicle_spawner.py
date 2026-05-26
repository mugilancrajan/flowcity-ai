from src.vehicle.vehicle import Vehicle, VehicleArchetype
from src.vehicle.vehicle_spawner import VehicleSpawner


# Default construction

def test_spawner_constructs_without_error():
    VehicleSpawner()


def test_all_four_archetypes_present_in_config():
    spawner = VehicleSpawner()
    assert VehicleArchetype.conservative in spawner._config
    assert VehicleArchetype.normal in spawner._config
    assert VehicleArchetype.aggressive in spawner._config
    assert VehicleArchetype.reckless in spawner._config


# create — identity

def test_create_returns_vehicle_instance():
    spawner = VehicleSpawner()
    v = spawner.create(1, (0, 0), (5, 5))
    assert isinstance(v, Vehicle)


def test_create_vehicle_id_matches():
    spawner = VehicleSpawner()
    v = spawner.create(1, (0, 0), (5, 5))
    assert v.id == 1


def test_create_vehicle_origin_matches():
    spawner = VehicleSpawner()
    v = spawner.create(1, (0, 0), (5, 5))
    assert v.origin == (0, 0)


def test_create_vehicle_destination_matches():
    spawner = VehicleSpawner()
    v = spawner.create(1, (0, 0), (5, 5))
    assert v.destination == (5, 5)


# create — speed_multiplier ranges

def test_conservative_speed_multiplier_in_range():
    spawner = VehicleSpawner()
    for i in range(100):
        v = spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.conservative)
        assert 0.75 <= v.speed_multiplier <= 0.95


def test_normal_speed_multiplier_in_range():
    spawner = VehicleSpawner()
    for i in range(100):
        v = spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.normal)
        assert 0.85 <= v.speed_multiplier <= 1.15


def test_aggressive_speed_multiplier_in_range():
    spawner = VehicleSpawner()
    for i in range(100):
        v = spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.aggressive)
        assert 1.1 <= v.speed_multiplier <= 1.35


def test_reckless_speed_multiplier_in_range():
    spawner = VehicleSpawner()
    for i in range(100):
        v = spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.reckless)
        assert 1.3 <= v.speed_multiplier <= 1.6


# create — following_distance ranges

def test_conservative_following_distance_in_range():
    spawner = VehicleSpawner()
    for i in range(100):
        v = spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.conservative)
        assert 1.75 <= v.following_distance <= 2.5


def test_normal_following_distance_in_range():
    spawner = VehicleSpawner()
    for i in range(100):
        v = spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.normal)
        assert 1.0 <= v.following_distance <= 2.0


def test_aggressive_following_distance_in_range():
    spawner = VehicleSpawner()
    for i in range(100):
        v = spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.aggressive)
        assert 0.5 <= v.following_distance <= 1.0


def test_reckless_following_distance_in_range():
    spawner = VehicleSpawner()
    for i in range(100):
        v = spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.reckless)
        assert 0.1 <= v.following_distance <= 0.5


# create — variance exists

def test_normal_speed_multiplier_has_variance():
    spawner = VehicleSpawner()
    values = {spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.normal).speed_multiplier for i in range(100)}
    assert len(values) > 1


def test_normal_following_distance_has_variance():
    spawner = VehicleSpawner()
    values = {spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.normal).following_distance for i in range(100)}
    assert len(values) > 1


# create — archetype distribution

def _count_archetypes(n):
    spawner = VehicleSpawner()
    counts = {a: 0 for a in VehicleArchetype}
    for i in range(n):
        v = spawner.create(i, (0, 0), (5, 5))
        counts[v.archetype] += 1
    return counts


def test_normal_count_greater_than_conservative():
    counts = _count_archetypes(10_000)
    assert counts[VehicleArchetype.normal] > counts[VehicleArchetype.conservative]


def test_normal_count_greater_than_aggressive():
    counts = _count_archetypes(10_000)
    assert counts[VehicleArchetype.normal] > counts[VehicleArchetype.aggressive]


def test_normal_count_greater_than_reckless():
    counts = _count_archetypes(10_000)
    assert counts[VehicleArchetype.normal] > counts[VehicleArchetype.reckless]


def test_reckless_count_less_than_conservative():
    counts = _count_archetypes(10_000)
    assert counts[VehicleArchetype.reckless] < counts[VehicleArchetype.conservative]


def test_reckless_count_less_than_aggressive():
    counts = _count_archetypes(10_000)
    assert counts[VehicleArchetype.reckless] < counts[VehicleArchetype.aggressive]


def test_conservative_and_aggressive_within_30_percent():
    counts = _count_archetypes(10_000)
    c = counts[VehicleArchetype.conservative]
    a = counts[VehicleArchetype.aggressive]
    assert max(c, a) / min(c, a) <= 1.3


# create_with_archetype

def test_create_with_archetype_returns_correct_archetype():
    spawner = VehicleSpawner()
    v = spawner.create_with_archetype(1, (0, 0), (5, 5), VehicleArchetype.aggressive)
    assert v.archetype == VehicleArchetype.aggressive


def test_create_with_archetype_speed_multiplier_has_variance():
    spawner = VehicleSpawner()
    values = {spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.aggressive).speed_multiplier for i in range(100)}
    assert len(values) > 1


# Overrides — speed

def test_speed_override_affects_overridden_archetype():
    spawner = VehicleSpawner(speed_overrides={VehicleArchetype.normal: (2.0, 2.5)})
    for i in range(100):
        v = spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.normal)
        assert 2.0 <= v.speed_multiplier <= 2.5


def test_speed_override_does_not_affect_other_archetypes():
    spawner = VehicleSpawner(speed_overrides={VehicleArchetype.normal: (2.0, 2.5)})
    for i in range(100):
        v = spawner.create_with_archetype(i, (0, 0), (5, 5), VehicleArchetype.conservative)
        assert 0.75 <= v.speed_multiplier <= 0.95


# Overrides — weights

def test_weight_override_makes_reckless_most_common():
    spawner = VehicleSpawner(weight_overrides={VehicleArchetype.reckless: 1000})
    counts = {a: 0 for a in VehicleArchetype}
    for i in range(1000):
        v = spawner.create(i, (0, 0), (5, 5))
        counts[v.archetype] += 1
    assert counts[VehicleArchetype.reckless] == max(counts.values())
