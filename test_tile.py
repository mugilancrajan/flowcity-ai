import sys
sys.path.insert(0, "src")

from world.tile import Tile, TileType, TrafficControl

passed = 0
failed = 0

def check(label, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {label}" + (f" — {detail}" if detail else ""))
    else:
        failed += 1
        print(f"  FAIL  {label}" + (f" — {detail}" if detail else ""))


print("=" * 60)
print("TEST 1 — Road tile at (3, 2): all properties")
print("=" * 60)
road = Tile(TileType.road, (3, 2))
print(f"  tile_type:       {road.tile_type}")
print(f"  position:        {road.position}")
print(f"  traffic_control: {road.traffic_control}")
print(f"  speed_limit:     {road.speed_limit}")
print(f"  capacity:        {road.capacity}")
print(f"  car_count:       {road.car_count}")
print(f"  car_speed:       {road.car_speed}")
check("tile_type is TileType.road",       road.tile_type == TileType.road)
check("position is (3, 2)",               road.position == (3, 2))
check("traffic_control defaults to none", road.traffic_control == TrafficControl.none)
check("speed_limit defaults to 3",        road.speed_limit == 3)
check("capacity defaults to 0",           road.capacity == 0)
check("car_count starts at 0",            road.car_count == 0)
check("car_speed starts at 0.0",          road.car_speed == 0.0)

print()
print("=" * 60)
print("TEST 2 — Residential tile: default speed_limit and capacity")
print("=" * 60)
res = Tile(TileType.residential, (0, 0))
print(f"  speed_limit: {res.speed_limit}")
print(f"  capacity:    {res.capacity}")
check("speed_limit defaults to 1",  res.speed_limit == 1)
check("capacity defaults to 0",     res.capacity == 0)
res_custom = Tile(TileType.residential, (1, 1), capacity=50)
check("capacity=50 stored correctly", res_custom.capacity == 50)

print()
print("=" * 60)
print("TEST 3 — Highway tile: speed_limit higher than road")
print("=" * 60)
highway = Tile(TileType.highway, (5, 5))
print(f"  highway speed_limit: {highway.speed_limit}")
print(f"  road    speed_limit: {road.speed_limit}")
check("highway speed_limit is 6",            highway.speed_limit == 6)
check("highway speed_limit > road speed_limit", highway.speed_limit > road.speed_limit)

print()
print("=" * 60)
print("TEST 4 — Congestion: car_count=3, car_speed=1.5 on road tile")
print("=" * 60)
road.car_count = 3
road.car_speed = 1.5
print(f"  car_count:  {road.car_count}")
print(f"  car_speed:  {road.car_speed}")
print(f"  speed_limit:{road.speed_limit}")
print(f"  congestion: {road.congestion}")
check("car_count is 3",           road.car_count == 3)
check("car_speed is 1.5",         road.car_speed == 1.5)
check("congestion is 0.5",        abs(road.congestion - 0.5) < 1e-9,
      f"got {road.congestion}")

print()
print("=" * 60)
print("TEST 5 — reset_live_data: car_count and car_speed return to 0")
print("=" * 60)
road.reset_live_data()
print(f"  car_count after reset: {road.car_count}")
print(f"  car_speed after reset: {road.car_speed}")
check("car_count is 0 after reset",   road.car_count == 0)
check("car_speed is 0.0 after reset", road.car_speed == 0.0)

print()
print("=" * 60)
print("TEST 6 — to_dict: correct keys, no live data")
print("=" * 60)
road.car_count = 99
road.car_speed = 9.9
d = road.to_dict()
print(f"  dict: {d}")
check("tile_type key present and correct",        d.get("tile_type") == "road")
check("traffic_control key present and correct",  d.get("traffic_control") == "none")
check("speed_limit key present and correct",      d.get("speed_limit") == 3)
check("position serialized as list",              d.get("position") == [3, 2])
check("capacity key present and correct",         d.get("capacity") == 0)
check("car_count NOT in dict",                    "car_count" not in d)
check("car_speed NOT in dict",                    "car_speed" not in d)

print()
print("=" * 60)
print("TEST 7 — from_dict: reconstructed tile matches original")
print("=" * 60)
road.reset_live_data()
original_dict = road.to_dict()
rebuilt = Tile.from_dict(original_dict)
print(f"  original dict: {original_dict}")
print(f"  rebuilt tile_type:       {rebuilt.tile_type}")
print(f"  rebuilt position:        {rebuilt.position}")
print(f"  rebuilt traffic_control: {rebuilt.traffic_control}")
print(f"  rebuilt speed_limit:     {rebuilt.speed_limit}")
print(f"  rebuilt capacity:        {rebuilt.capacity}")
check("tile_type matches",       rebuilt.tile_type == road.tile_type)
check("position matches",        rebuilt.position == road.position)
check("traffic_control matches", rebuilt.traffic_control == road.traffic_control)
check("speed_limit matches",     rebuilt.speed_limit == road.speed_limit)
check("capacity matches",        rebuilt.capacity == road.capacity)
check("rebuilt car_count starts at 0",   rebuilt.car_count == 0)
check("rebuilt car_speed starts at 0.0", rebuilt.car_speed == 0.0)

print()
print("=" * 60)
print("TEST 8 — Empty tile: congestion returns 0.0 without crashing")
print("=" * 60)
empty = Tile(TileType.empty, (0, 0))
print(f"  speed_limit: {empty.speed_limit}")
try:
    cong = empty.congestion
    print(f"  congestion:  {cong}")
    check("congestion returns 0.0 (no crash)", cong == 0.0,
          f"got {cong}")
except ZeroDivisionError:
    failed += 1
    print("  FAIL  congestion raised ZeroDivisionError")

print()
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 60)
