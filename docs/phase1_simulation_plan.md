# Phase 1 Plan — Simulation Engine

## Files to Create
- `src/simulation/spawn_manager.py`
- `src/simulation/simulation_engine.py`
- `tests/test_spawn_manager.py`
- `tests/test_simulation_engine.py`

---

## SpawnManager — `src/simulation/spawn_manager.py`

### `__init__(world, road_network, vehicle_spawner)`
- Stores all three references
- Builds `_residential_tiles`, `_commercial_tiles`, `_workplace_tiles` via `world.get_tiles_by_type()`
- Sets `_ticks_since_last_spawn = 0`
- Sets `_spawn_accumulator = 0.0` (fractional counter for rate-based spawning)

### `_get_current_period(tick)`
- `day_tick = tick % TICKS_PER_DAY`
- Iterates `TIME_PERIODS`, returns the key whose `start_tick <= day_tick <= end_tick`

### `_should_spawn(tick, period)`
- Rate = `SPAWN_RATES[period]` vehicles per simulated minute; 1 simulated minute = `TICKS_PER_SIMULATED_MINUTE` ticks
- If rate == 0: return False
- Each call adds `rate / TICKS_PER_SIMULATED_MINUTE` to `_spawn_accumulator`
- When accumulator >= 1.0: subtract 1.0, return True
- Otherwise: return False

### `_get_zone_tiles(zone_type_string)`
- Maps `"residential"` → `_residential_tiles`, `"commercial"` → `_commercial_tiles`, `"workplace"` → `_workplace_tiles`
- Unknown string → `[]`

### `get_spawn(tick, next_vehicle_id)`
- Gets period via `_get_current_period(tick)`
- Calls `_should_spawn(tick, period)` — if False, increments `_ticks_since_last_spawn`, returns None
- Gets `SPAWN_ZONE_WEIGHTS[period]`, selects `(origin_zone, dest_zone)` pair via `random.choices` with weights
- Gets tile lists for each zone; if either is empty → return None
- Picks one random tile from each list; if same tile object → return None
- Calls `road_network.get_path(origin.position, destination.position)` — catches `NoPathError` → return None
- Creates vehicle via `vehicle_spawner.create(next_vehicle_id, origin.position, destination.position, spawn_tick=tick)`
- Assigns returned path to `vehicle.path`
- Sets `vehicle.state = VehicleState.driving`
- Resets `_ticks_since_last_spawn = 0`
- Returns the vehicle

### `update_world(world)`
- Rebuilds `_residential_tiles`, `_commercial_tiles`, `_workplace_tiles` from the new world

---

## SimulationEngine — `src/simulation/simulation_engine.py`

### `__init__(world)`
- Stores world reference
- Creates `RoadNetwork(world)` → `_road_network`
- Creates `VehicleSpawner()` with default config → `_vehicle_spawner`
- Creates `SpawnManager(world, _road_network, _vehicle_spawner)` → `_spawn_manager`
- Sets `_tick = 0`
- Sets `_running = False`
- Sets `_speed = DEFAULT_SPEED`
- Sets `_active_vehicles = []`
- Sets `_next_vehicle_id = 1`
- Sets `_total_trips_completed = 0`
- Sets `_total_spawned = 0`
- Sets `_completed_trip_ticks = []`
- Sets `_trips_this_interval = 0`
- Sets `_metrics_snapshots = []`

### Read-only properties
- `tick` → `_tick`
- `running` → `_running`
- `speed` → `_speed`
- `active_vehicles` → `_active_vehicles`
- `total_trips_completed` → `_total_trips_completed`
- `total_spawned` → `_total_spawned`
- `metrics_snapshots` → `_metrics_snapshots`
- `time_of_day` → derived string (see below)
- `current_period` → derived string from `_spawn_manager._get_current_period(tick)`

### `time_of_day` calculation
- `day_tick = tick % TICKS_PER_DAY`
- `total_minutes = day_tick // TICKS_PER_SIMULATED_MINUTE`
- `hours = (total_minutes // 60) % 24`
- `minutes = total_minutes % 60`
- Convert to 12-hour AM/PM format: `"06:30 AM"`, `"12:00 PM"`, `"12:00 AM"`

### `start()`
- Calls `_road_network.rebuild(world)` to rebuild graph from current world
- Calls `_spawn_manager.update_world(world)` to rebuild tile lists
- Resets `_tick = 0`
- Clears `_active_vehicles = []`
- Clears `_metrics_snapshots = []`
- Resets `_total_trips_completed = 0`, `_total_spawned = 0`, `_next_vehicle_id = 1`
- Resets `_completed_trip_ticks = []`, `_trips_this_interval = 0`
- Sets `_running = True`

### `pause()`
- Sets `_running = False`

### `resume()`
- Sets `_running = True`

### `reset()`
- Sets `_running = False`
- Resets `_tick = 0`
- Clears `_active_vehicles = []`
- Clears `_metrics_snapshots = []`
- Resets `_total_trips_completed = 0`, `_total_spawned = 0`, `_next_vehicle_id = 1`
- Resets `_completed_trip_ticks = []`, `_trips_this_interval = 0`
- Does NOT modify world or rebuild road network

### `set_speed(speed)`
- Raises `ValueError` if `speed not in {SPEED_SLOW, SPEED_NORMAL, SPEED_FAST, SPEED_ULTRA}`
- Sets `_speed = speed`

### `step()` — six ordered phases

**Phase 1 — Spawn**
- Calls `_spawn_manager.get_spawn(_tick, _next_vehicle_id)`
- If a vehicle is returned: append to `_active_vehicles`, increment `_next_vehicle_id`, increment `_total_spawned`

**Phase 2 — Movement**
For each vehicle in `_active_vehicles` where `state == VehicleState.driving`:
- `col, row = int(vehicle.position[0]), int(vehicle.position[1])`
- `tile = world.get_tile(col, row)`
- `desired_speed = tile.speed_limit * MOVEMENT_SCALE * vehicle.speed_multiplier`
- `vehicle.desired_speed = desired_speed`
- Look ahead starting at `vehicle.path_index + 1`, up to `int(vehicle.following_distance)` tiles forward from that point (range: path_index+1 to path_index+1+int(following_distance), clamped to len(path))
- For each tile in that lookahead range, check `world.get_tile(*path_tile).car_count`
- If any has `car_count > 0`:
  - `distance = lookahead_index + 1` (steps ahead)
  - `current_speed = max(0.0, desired_speed * (distance / vehicle.following_distance))`
- If none: `current_speed = desired_speed`
- `vehicle.current_speed = current_speed`
- If `vehicle.path_index + 1 < len(vehicle.path)`:
  - `target = vehicle.path[vehicle.path_index + 1]`
  - `dx = target[0] - vehicle.position[0]`, `dy = target[1] - vehicle.position[1]`
  - `magnitude = sqrt(dx*dx + dy*dy)`
  - If magnitude > 0: `direction = (dx/magnitude, dy/magnitude)` else `(0, 0)`
  - `new_pos = (vehicle.position[0] + direction[0] * current_speed, vehicle.position[1] + direction[1] * current_speed)`
  - `vehicle.position = new_pos`
  - `dist_to_next = sqrt((new_pos[0]-target[0])**2 + (new_pos[1]-target[1])**2)`
  - If `dist_to_next < 0.1`:
    - Snap: `vehicle.position = (float(target[0]), float(target[1]))`
    - `vehicle.path_index += 1`
    - If `vehicle.path_index >= len(vehicle.path) - 1`: `vehicle.state = VehicleState.arrived`

**Phase 3 — Spawning state transition**
- For each vehicle with `state == VehicleState.spawning`: set `state = VehicleState.driving`

**Phase 4 — Arrival**
- Collect all vehicles with `state == VehicleState.arrived`
- For each: `trip_duration = _tick - vehicle.spawn_tick`, append to `_completed_trip_ticks`, increment `_total_trips_completed`, increment `_trips_this_interval`
- Remove all arrived vehicles from `_active_vehicles`

**Phase 5 — Tile live data**
- For every tile in world: `tile.car_count = 0`, `tile.car_speed = 0.0`
- First pass — accumulate: for each driving vehicle, get tile at `int(vehicle.position)`, increment `tile.car_count`, add `vehicle.current_speed` to `tile.car_speed`
- Second pass — average: for each tile with `car_count > 0`: `tile.car_speed = tile.car_speed / tile.car_count`

**Phase 6 — Metrics**
- If `_tick % METRICS_SNAPSHOT_INTERVAL == 0`: build and append snapshot (see below), reset `_trips_this_interval = 0`
- Increment `_tick` by 1
- If `_tick >= TICKS_PER_DAY`: reset `_tick = 0`

### Metrics snapshot dict

```python
{
    "tick": _tick,
    "total_trips_completed": _total_trips_completed,
    "trips_this_interval": _trips_this_interval,
    "active_vehicles": len(_active_vehicles),
    "total_spawned": _total_spawned,
    "average_travel_time": mean(_completed_trip_ticks) if any else 0.0,
    "congestion_index": <calculated>,
    "average_speed_ratio": <calculated>,
    "city_health_score": <calculated>,
    "top_congested_tiles": <calculated>,
}
```

**congestion_index:**
- Get all road and highway tiles from world
- Filter to tiles where `speed_limit > 0 and car_count > 0`
- `ratio = tile.car_speed / tile.speed_limit` for each
- `congestion_index = mean(1 - ratio) * 100`
- If no qualifying tiles: `0.0`

**average_speed_ratio:**
- Same road/highway tiles with `car_count > 0 and speed_limit > 0`
- `mean(tile.car_speed / tile.speed_limit)`
- If none: `0.0`

**city_health_score:**
- `throughput_rate = min(1.0, (_trips_this_interval / METRICS_SNAPSHOT_INTERVAL))`
- `inverse_congestion = 1.0 - (congestion_index / 100)`
- `score = (throughput_rate * 0.4 + average_speed_ratio * 0.35 + inverse_congestion * 0.25) * 100`
- Clamp to 0–100

**top_congested_tiles:**
- All road/highway tiles with `speed_limit > 0 and car_count > 0`
- `congestion_ratio = 1.0 - (tile.car_speed / tile.speed_limit)`
- Sort descending, return top 5 as `[(col, row, congestion_ratio), ...]`

---

## Tests — `tests/test_spawn_manager.py`

**Helper:** `make_city_world()` — 5×1 world: residential(0,0) - road(1,0) - road(2,0) - road(3,0) - workplace(4,0)

**Construction**
- Constructs without error on valid city world
- Constructs without error on all-empty world

**Time period detection** (7 ticks)
- Tick 0 → `"early_morning"`
- Tick 3,600 → `"morning_rush"`
- Tick 5,400 → `"midday"`
- Tick 9,600 → `"evening_rush"`
- Tick 11,400 → `"night"`
- Tick 14,399 → `"night"`
- Tick 14,400 → `"early_morning"` (wraps)

**Spawn behavior**
- Returns None on world with no residential tiles during morning_rush tick
- Returns None on world with no workplace tiles during morning_rush tick
- Returns a Vehicle on valid city world after enough ticks pass
- Returned vehicle origin is a valid tile position in the world
- Returned vehicle destination is a valid tile position in the world
- Returned vehicle has non-empty path
- Returned vehicle path first element matches origin
- Returned vehicle path last element matches destination
- Returned vehicle state is `VehicleState.driving`

**update_world**
- After `update_world` with new world containing residential tiles, spawn becomes possible

---

## Tests — `tests/test_simulation_engine.py`

**Helper:** `make_engine()` — same 5×1 city layout, returns `SimulationEngine(w)`

**Construction**
- Constructs without error
- Initial tick is 0
- Initial running is False
- Initial active_vehicles is empty list
- Initial speed equals `DEFAULT_SPEED`
- Initial total_trips_completed is 0
- Initial total_spawned is 0

**start / pause / resume / reset**
- After `start()`, running is True
- After `start()`, tick is 0
- After `start()` then `pause()`, running is False
- After `pause()` then `resume()`, running is True
- After `start()` + 10 `step()` calls + `start()` again, tick resets to 0
- After `reset()`, running is False
- After `reset()`, tick is 0
- After `reset()`, active_vehicles is empty
- After `reset()`, total_trips_completed is 0

**set_speed**
- `set_speed(SPEED_FAST)` sets speed to `SPEED_FAST`
- `set_speed(SPEED_SLOW)` sets speed to `SPEED_SLOW`
- `set_speed(99999)` raises `ValueError`

**time_of_day**
- Tick 0 → `"12:00 AM"`
- Tick 600 → `"01:00 AM"`
- Tick 3,600 → `"06:00 AM"`
- Tick 7,200 → `"12:00 PM"`
- Tick 10,800 → `"06:00 PM"`

**current_period**
- Tick 0 → `"early_morning"`
- Tick 3,600 → `"morning_rush"`
- Tick 9,600 → `"evening_rush"`

**step() — tick advancement**
- After one `step()`, tick is 1
- After 14,400 `step()` calls, tick resets to 0
- `step()` works when running is False

**step() — spawning**
- After stepping through a full morning_rush period (ticks 3,600–5,399), total_spawned > 0
- All active vehicles are `Vehicle` instances
- Each active vehicle has a non-empty path

**step() — movement**
- After spawning a vehicle and stepping, vehicle position changes from its origin
- Vehicle position is always a float tuple
- Vehicle path_index never exceeds `len(path) - 1`

**step() — arrival**
- total_trips_completed increases after vehicles arrive
- Arrived vehicles are not in active_vehicles

**step() — tile live data**
- After a step with active driving vehicles, at least one tile has car_count > 0
- After all vehicles arrive and one more step, all tile car_counts are 0

**step() — metrics**
- After `METRICS_SNAPSHOT_INTERVAL` steps, metrics_snapshots has exactly 1 entry
- After `2 * METRICS_SNAPSHOT_INTERVAL` steps, metrics_snapshots has exactly 2 entries
- Each snapshot has all required keys
- city_health_score is between 0 and 100
- congestion_index is between 0 and 100
- top_congested_tiles is a list of at most 5 tuples

**reset() — world unchanged**
- After running simulation and resetting, world tiles are unchanged

---

## Open Question

The briefing says `_should_spawn` uses "a counter and fractional accumulator approach" and says the counter increments when not spawning. My plan uses `_spawn_accumulator` (float) that grows by `rate / TICKS_PER_SIMULATED_MINUTE` each call, triggering when >= 1.0, plus `_ticks_since_last_spawn` that resets on spawn. Awaiting confirmation this interpretation is correct before proceeding.
