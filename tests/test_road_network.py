import pytest
from src.world.world import World
from src.world.tile import TileType, TrafficControl
from src.graph.road_network import RoadNetwork
from src.exceptions import NoPathError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_world(cols: int, rows: int) -> World:
    return World(cols, rows)


def set_road(world: World, col: int, row: int) -> None:
    world.set_tile(col, row, tile_type=TileType.road)


def set_empty(world: World, col: int, row: int) -> None:
    world.set_tile(col, row, tile_type=TileType.empty)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_build_valid_world():
    world = make_world(3, 3)
    set_road(world, 1, 1)
    rn = RoadNetwork(world)
    assert rn.graph is not None


def test_all_empty_world_has_no_nodes():
    world = make_world(3, 3)
    rn = RoadNetwork(world)
    assert rn.graph.number_of_nodes() == 0


def test_one_road_tile_has_one_node():
    world = make_world(3, 3)
    set_road(world, 1, 1)
    rn = RoadNetwork(world)
    assert rn.graph.number_of_nodes() == 1
    assert (1, 1) in rn.graph


def test_mixed_tile_types_correct_node_count():
    world = make_world(3, 3)
    world.set_tile(0, 0, tile_type=TileType.road)
    world.set_tile(1, 0, tile_type=TileType.highway)
    world.set_tile(2, 0, tile_type=TileType.residential)
    world.set_tile(0, 1, tile_type=TileType.commercial)
    world.set_tile(1, 1, tile_type=TileType.workplace)
    # (2,1), (0,2), (1,2), (2,2) remain empty
    rn = RoadNetwork(world)
    assert rn.graph.number_of_nodes() == 5


def test_node_attributes_match_tile():
    world = make_world(3, 3)
    world.set_tile(1, 1, tile_type=TileType.road, traffic_control=TrafficControl.stop_sign, speed_limit=5)
    rn = RoadNetwork(world)
    attrs = rn.graph.nodes[(1, 1)]
    assert attrs["tile_type"] == TileType.road
    assert attrs["speed_limit"] == 5
    assert attrs["traffic_control"] == TrafficControl.stop_sign


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------

def test_adjacent_road_tiles_have_edges_both_directions():
    world = make_world(3, 3)
    set_road(world, 0, 0)
    set_road(world, 1, 0)
    rn = RoadNetwork(world)
    assert rn.graph.has_edge((0, 0), (1, 0))
    assert rn.graph.has_edge((1, 0), (0, 0))


def test_diagonal_tiles_have_no_edge():
    world = make_world(3, 3)
    set_road(world, 0, 0)
    set_road(world, 1, 1)
    rn = RoadNetwork(world)
    assert not rn.graph.has_edge((0, 0), (1, 1))
    assert not rn.graph.has_edge((1, 1), (0, 0))


def test_empty_tile_between_two_road_tiles_no_direct_edge():
    # (0,0) road -- (1,0) empty -- (2,0) road
    world = make_world(3, 1)
    set_road(world, 0, 0)
    set_road(world, 2, 0)
    rn = RoadNetwork(world)
    assert not rn.graph.has_edge((0, 0), (2, 0))
    assert not rn.graph.has_edge((2, 0), (0, 0))


def test_edge_weight_is_one():
    world = make_world(2, 1)
    set_road(world, 0, 0)
    set_road(world, 1, 0)
    rn = RoadNetwork(world)
    assert rn.graph[(0, 0)][(1, 0)]["weight"] == 1
    assert rn.graph[(1, 0)][(0, 0)]["weight"] == 1


def test_road_adjacent_to_residential_has_edges_both_directions():
    world = make_world(2, 1)
    set_road(world, 0, 0)
    world.set_tile(1, 0, tile_type=TileType.residential)
    rn = RoadNetwork(world)
    assert rn.graph.has_edge((0, 0), (1, 0))
    assert rn.graph.has_edge((1, 0), (0, 0))


# ---------------------------------------------------------------------------
# get_path — valid
# ---------------------------------------------------------------------------

def test_get_path_returns_list_of_tuples():
    world = make_world(3, 1)
    set_road(world, 0, 0)
    set_road(world, 1, 0)
    set_road(world, 2, 0)
    rn = RoadNetwork(world)
    path = rn.get_path((0, 0), (2, 0))
    assert isinstance(path, list)
    assert all(isinstance(p, tuple) and len(p) == 2 for p in path)


def test_get_path_first_is_origin_last_is_destination():
    world = make_world(3, 1)
    set_road(world, 0, 0)
    set_road(world, 1, 0)
    set_road(world, 2, 0)
    rn = RoadNetwork(world)
    path = rn.get_path((0, 0), (2, 0))
    assert path[0] == (0, 0)
    assert path[-1] == (2, 0)


def test_get_path_contains_only_non_empty_tiles():
    world = make_world(3, 1)
    set_road(world, 0, 0)
    set_road(world, 1, 0)
    set_road(world, 2, 0)
    rn = RoadNetwork(world)
    path = rn.get_path((0, 0), (2, 0))
    for node in path:
        assert node in rn.graph


def test_get_path_returns_shortest_path():
    # Layout (3x2 grid):
    #   (0,0)-(1,0)-(2,0)
    #     |           |
    #   (0,1)-(1,1)-(2,1)
    # Shortest from (0,0) to (2,0) is length 3: (0,0)->(1,0)->(2,0)
    world = make_world(3, 2)
    for col in range(3):
        set_road(world, col, 0)
        set_road(world, col, 1)
    rn = RoadNetwork(world)
    path = rn.get_path((0, 0), (2, 0))
    assert len(path) == 3


def test_get_path_origin_equals_destination():
    world = make_world(2, 2)
    set_road(world, 0, 0)
    rn = RoadNetwork(world)
    path = rn.get_path((0, 0), (0, 0))
    assert path == [(0, 0)]


# ---------------------------------------------------------------------------
# get_path — invalid
# ---------------------------------------------------------------------------

def test_get_path_origin_not_in_graph_raises():
    world = make_world(3, 3)
    set_road(world, 2, 2)
    rn = RoadNetwork(world)
    with pytest.raises(NoPathError):
        rn.get_path((0, 0), (2, 2))


def test_get_path_destination_not_in_graph_raises():
    world = make_world(3, 3)
    set_road(world, 0, 0)
    rn = RoadNetwork(world)
    with pytest.raises(NoPathError):
        rn.get_path((0, 0), (2, 2))


def test_get_path_disconnected_origin_raises():
    # (0,0) and (2,0) are both in the graph but separated by an empty tile
    world = make_world(3, 1)
    set_road(world, 0, 0)
    set_road(world, 2, 0)
    rn = RoadNetwork(world)
    with pytest.raises(NoPathError):
        rn.get_path((0, 0), (2, 0))


def test_get_path_disconnected_destination_raises():
    # Same disconnected graph, reversed direction
    world = make_world(3, 1)
    set_road(world, 0, 0)
    set_road(world, 2, 0)
    rn = RoadNetwork(world)
    with pytest.raises(NoPathError):
        rn.get_path((2, 0), (0, 0))


# ---------------------------------------------------------------------------
# rebuild
# ---------------------------------------------------------------------------

def test_rebuild_adds_new_node():
    world = make_world(3, 3)
    rn = RoadNetwork(world)
    assert (1, 1) not in rn.graph
    set_road(world, 1, 1)
    rn.rebuild(world)
    assert (1, 1) in rn.graph


def test_rebuild_removes_node():
    world = make_world(3, 3)
    set_road(world, 1, 1)
    rn = RoadNetwork(world)
    assert (1, 1) in rn.graph
    set_empty(world, 1, 1)
    rn.rebuild(world)
    assert (1, 1) not in rn.graph


def test_rebuild_unrelated_nodes_unchanged():
    world = make_world(3, 3)
    set_road(world, 0, 0)
    set_road(world, 2, 2)
    rn = RoadNetwork(world)
    assert (0, 0) in rn.graph
    assert (2, 2) in rn.graph
    # Add a new tile and rebuild — unrelated nodes must still be present
    set_road(world, 1, 1)
    rn.rebuild(world)
    assert (0, 0) in rn.graph
    assert (2, 2) in rn.graph
    assert (1, 1) in rn.graph
