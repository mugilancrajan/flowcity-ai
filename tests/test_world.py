import pytest
from src.world.tile import TileType, TrafficControl
from src.world.world import World


# --- Construction ---

def test_world_correct_dimensions():
    w = World(10, 8)
    assert w.cols == 10 and w.rows == 8

def test_world_all_tiles_empty_on_init():
    w = World(10, 8)
    for row in range(8):
        for col in range(10):
            assert w.get_tile(col, row).tile_type == TileType.empty

def test_world_cols_rows_properties():
    w = World(5, 3)
    assert w.cols == 5
    assert w.rows == 3

def test_world_1x1_succeeds():
    w = World(1, 1)
    assert w.cols == 1 and w.rows == 1

def test_world_zero_cols_raises():
    with pytest.raises(ValueError):
        World(0, 5)

def test_world_zero_rows_raises():
    with pytest.raises(ValueError):
        World(5, 0)

def test_world_negative_cols_raises():
    with pytest.raises(ValueError):
        World(-1, 5)


# --- get_tile valid ---

def test_get_tile_top_left():
    w = World(10, 8)
    tile = w.get_tile(0, 0)
    assert tile is not None

def test_get_tile_bottom_right():
    w = World(10, 8)
    tile = w.get_tile(9, 7)
    assert tile is not None

def test_get_tile_correct_position():
    w = World(5, 5)
    tile = w.get_tile(3, 2)
    assert tile.position == (3, 2)


# --- get_tile invalid ---

def test_get_tile_negative_col_raises():
    w = World(5, 5)
    with pytest.raises(IndexError):
        w.get_tile(-1, 0)

def test_get_tile_negative_row_raises():
    w = World(5, 5)
    with pytest.raises(IndexError):
        w.get_tile(0, -1)

def test_get_tile_col_at_bound_raises():
    w = World(5, 5)
    with pytest.raises(IndexError):
        w.get_tile(5, 0)

def test_get_tile_row_at_bound_raises():
    w = World(5, 5)
    with pytest.raises(IndexError):
        w.get_tile(0, 5)


# --- set_tile ---

def test_set_tile_type_reflected():
    w = World(5, 5)
    w.set_tile(2, 3, tile_type=TileType.road)
    assert w.get_tile(2, 3).tile_type == TileType.road

def test_set_tile_does_not_affect_neighbors():
    w = World(5, 5)
    w.set_tile(2, 2, tile_type=TileType.road)
    assert w.get_tile(1, 2).tile_type == TileType.empty
    assert w.get_tile(3, 2).tile_type == TileType.empty
    assert w.get_tile(2, 1).tile_type == TileType.empty
    assert w.get_tile(2, 3).tile_type == TileType.empty

def test_set_tile_out_of_bounds_raises():
    w = World(5, 5)
    with pytest.raises(IndexError):
        w.set_tile(10, 10, tile_type=TileType.road)

def test_set_tile_type_only_does_not_reset_speed_limit():
    w = World(5, 5)
    w.set_tile(1, 1, speed_limit=99)
    w.set_tile(1, 1, tile_type=TileType.road)
    assert w.get_tile(1, 1).speed_limit == 99


# --- get_tiles_by_type ---

def test_get_tiles_by_type_all_empty():
    w = World(4, 3)
    tiles = w.get_tiles_by_type(TileType.empty)
    assert len(tiles) == 4 * 3

def test_get_tiles_by_type_no_roads_on_fresh_world():
    w = World(4, 3)
    assert w.get_tiles_by_type(TileType.road) == []

def test_get_tiles_by_type_after_setting_roads():
    w = World(5, 5)
    w.set_tile(0, 0, tile_type=TileType.road)
    w.set_tile(1, 0, tile_type=TileType.road)
    w.set_tile(2, 0, tile_type=TileType.road)
    assert len(w.get_tiles_by_type(TileType.road)) == 3

def test_get_tiles_by_type_correct_positions():
    w = World(5, 5)
    w.set_tile(2, 3, tile_type=TileType.road)
    tiles = w.get_tiles_by_type(TileType.road)
    assert tiles[0].position == (2, 3)


# --- get_neighbors ---

def test_get_neighbors_center_returns_4():
    w = World(5, 5)
    assert len(w.get_neighbors(2, 2)) == 4

def test_get_neighbors_corner_returns_2():
    w = World(5, 5)
    assert len(w.get_neighbors(0, 0)) == 2

def test_get_neighbors_edge_non_corner_returns_3():
    w = World(5, 5)
    assert len(w.get_neighbors(2, 0)) == 3

def test_get_neighbors_correct_positions():
    w = World(5, 5)
    neighbors = w.get_neighbors(2, 2)
    positions = {n.position for n in neighbors}
    assert positions == {(2, 1), (2, 3), (1, 2), (3, 2)}

def test_get_neighbors_1x1_returns_empty():
    w = World(1, 1)
    assert w.get_neighbors(0, 0) == []


# --- Persistence ---

def test_to_dict_from_dict_round_trip_dimensions_and_types():
    w = World(4, 3)
    w.set_tile(1, 2, tile_type=TileType.road)
    w2 = World.from_dict(w.to_dict())
    assert w2.cols == w.cols and w2.rows == w.rows
    for row in range(w.rows):
        for col in range(w.cols):
            assert w2.get_tile(col, row).tile_type == w.get_tile(col, row).tile_type

def test_round_trip_preserves_speed_limits_and_traffic_controls():
    w = World(3, 3)
    w.set_tile(1, 1, tile_type=TileType.road, speed_limit=5, traffic_control=TrafficControl.stop_sign)
    w2 = World.from_dict(w.to_dict())
    tile = w2.get_tile(1, 1)
    assert tile.speed_limit == 5
    assert tile.traffic_control == TrafficControl.stop_sign

def test_save_load_round_trip(tmp_path):
    w = World(3, 4)
    w.set_tile(0, 0, tile_type=TileType.highway)
    path = tmp_path / "world.json"
    w.save(path)
    w2 = World.load(path)
    assert w2.cols == 3 and w2.rows == 4
    assert w2.get_tile(0, 0).tile_type == TileType.highway

def test_from_dict_missing_tiles_key_raises():
    with pytest.raises(ValueError):
        World.from_dict({"cols": 3, "rows": 3})

def test_from_dict_missing_cols_key_raises():
    with pytest.raises(ValueError):
        World.from_dict({"rows": 3, "tiles": []})

def test_from_dict_missing_rows_key_raises():
    with pytest.raises(ValueError):
        World.from_dict({"cols": 3, "tiles": []})
