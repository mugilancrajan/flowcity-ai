import bisect
import math
import random

from src.config import (
    DEFAULT_SPEED, SPEED_SLOW, SPEED_NORMAL, SPEED_FAST, SPEED_ULTRA,
    TICKS_PER_DAY, TICKS_PER_SIMULATED_MINUTE, MOVEMENT_SCALE,
    METRICS_SNAPSHOT_INTERVAL,
    VEHICLE_MIN_GAP, ARCHETYPE_CONFIGS,
    CORNER_DECEL_DISTANCE, CORNER_SPEED_FRACTION,
    TRAFFIC_LIGHT_CYCLE, TRAFFIC_LIGHT_GREEN_TICKS,
    STOP_SIGN_WAIT_TICKS,
)
from src.world.tile import TileType, TrafficControl
from src.graph.road_network import RoadNetwork
from src.vehicle.vehicle import VehicleState
from src.vehicle.vehicle_spawner import VehicleSpawner
from src.simulation.spawn_manager import SpawnManager

_VALID_SPEEDS = {SPEED_SLOW, SPEED_NORMAL, SPEED_FAST, SPEED_ULTRA}

# Base physics rates — per-archetype multipliers (accel_mult/decel_mult) are
# applied on top of these in ARCHETYPE_CONFIGS (config.py).
_ACCEL_RATE         = 0.12  # base acceleration fraction of desired_speed per tick
_DECEL_RATE         = 0.35  # base deceleration fraction of desired_speed per tick
_MIN_SPEED_FRACTION = 0.0   # vehicles may come to a complete stop when blocked
_GAP_SCAN_K         = 20    # max vehicles to inspect ahead in the sorted gap-scan


class SimulationEngine:
    def __init__(self, world):
        self._world = world
        self._road_network = RoadNetwork(world)
        self._vehicle_spawner = VehicleSpawner()
        self._spawn_manager = SpawnManager(world, self._road_network, self._vehicle_spawner)
        self._tick = 0
        self._running = False
        self._speed = DEFAULT_SPEED
        self._active_vehicles = []
        self._next_vehicle_id = 1
        self._total_trips_completed = 0
        self._total_spawned = 0
        self._completed_trip_ticks = []
        self._trips_this_interval = 0
        self._metrics_snapshots = []
        # Per-vehicle stop-sign state (keyed by id(vehicle))
        self._stop_wait: dict[int, int] = {}    # remaining hold ticks
        self._stop_served: dict[int, set] = {}  # tile positions already served

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def tick(self):
        return self._tick

    @property
    def running(self):
        return self._running

    @property
    def speed(self):
        return self._speed

    @property
    def active_vehicles(self):
        return self._active_vehicles

    @property
    def total_trips_completed(self):
        return self._total_trips_completed

    @property
    def total_spawned(self):
        return self._total_spawned

    @property
    def metrics_snapshots(self):
        return self._metrics_snapshots

    @property
    def time_of_day(self):
        day_tick = self._tick % TICKS_PER_DAY
        total_minutes = day_tick // TICKS_PER_SIMULATED_MINUTE
        hours = (total_minutes // 60) % 24
        minutes = total_minutes % 60
        period = "AM" if hours < 12 else "PM"
        display_hour = hours % 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour:02d}:{minutes:02d} {period}"

    @property
    def current_period(self):
        return self._spawn_manager._get_current_period(self._tick)

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def start(self):
        self._road_network.rebuild(self._world)
        self._spawn_manager.update_world(self._world)
        self._tick = 0
        self._active_vehicles = []
        self._metrics_snapshots = []
        self._total_trips_completed = 0
        self._total_spawned = 0
        self._next_vehicle_id = 1
        self._completed_trip_ticks = []
        self._trips_this_interval = 0
        self._stop_wait = {}
        self._stop_served = {}
        self._running = True

    def pause(self):
        self._running = False

    def resume(self):
        self._running = True

    def reset(self):
        self._running = False
        self._tick = 0
        self._active_vehicles = []
        self._metrics_snapshots = []
        self._total_trips_completed = 0
        self._total_spawned = 0
        self._next_vehicle_id = 1
        self._completed_trip_ticks = []
        self._trips_this_interval = 0
        self._stop_wait = {}
        self._stop_served = {}

    def set_speed(self, speed):
        if speed not in _VALID_SPEEDS:
            raise ValueError(f"Invalid speed: {speed!r}. Must be one of {_VALID_SPEEDS}")
        self._speed = speed

    # ------------------------------------------------------------------
    # Simulation step
    # ------------------------------------------------------------------

    def step(self):
        # Phase 1 — Spawn (with spawn-block: never place a vehicle on top of another)
        vehicle = self._spawn_manager.get_spawn(self._tick, self._next_vehicle_id)
        if vehicle is not None:
            spx, spy = vehicle.position
            spawn_blocked = any(
                ov.state == VehicleState.driving and
                math.sqrt((ov.position[0] - spx) ** 2 + (ov.position[1] - spy) ** 2)
                < VEHICLE_MIN_GAP
                for ov in self._active_vehicles
            )
            if not spawn_blocked:
                self._active_vehicles.append(vehicle)
                self._next_vehicle_id += 1
                self._total_spawned += 1

        # Phase 2 — Movement
        #
        # Pre-compute each driving vehicle's normalised direction vector once
        # per tick (O(n)) so the gap-scan never recomputes a sqrt per pair.
        _dirs: dict[int, tuple[float, float]] = {}
        for _v in self._active_vehicles:
            if _v.state != VehicleState.driving:
                continue
            _path = _v.path
            _idx  = _v.path_index
            if _idx + 1 < len(_path):
                _nxt = _path[_idx + 1]
                _dx  = _nxt[0] - _v.position[0]
                _dy  = _nxt[1] - _v.position[1]
                _m   = math.sqrt(_dx * _dx + _dy * _dy)
                _dirs[id(_v)] = (_dx / _m, _dy / _m) if _m > 0 else (1.0, 0.0)
            elif _idx > 0:
                _dx = _path[_idx][0] - _path[_idx - 1][0]
                _dy = _path[_idx][1] - _path[_idx - 1][1]
                _m  = math.sqrt(_dx * _dx + _dy * _dy)
                _dirs[id(_v)] = (_dx / _m, _dy / _m) if _m > 0 else (1.0, 0.0)
            else:
                _dirs[id(_v)] = (1.0, 0.0)

        # Build sorted groups by cardinal direction so the gap-scan is O(n log n)
        # instead of O(n²). Each vehicle is bucketed by its dominant movement axis
        # and sorted by its projected position along that axis. This lets each
        # vehicle binary-search for vehicles strictly ahead, then inspect only the
        # nearest _GAP_SCAN_K candidates — not every other vehicle.
        _cg: dict[tuple[int, int], list] = {
            (1, 0): [], (-1, 0): [], (0, 1): [], (0, -1): []
        }
        for _v in self._active_vehicles:
            if _v.state != VehicleState.driving:
                continue
            _vdx, _vdy = _dirs[id(_v)]
            if abs(_vdx) >= abs(_vdy):
                _gk = (1, 0) if _vdx >= 0 else (-1, 0)
            else:
                _gk = (0, 1) if _vdy >= 0 else (0, -1)
            _cg[_gk].append((_v.position[0] * _gk[0] + _v.position[1] * _gk[1], id(_v), _v))

        _sg: dict[tuple[int, int], tuple[list, list]] = {}
        for _gk, _ents in _cg.items():
            if _ents:
                _ents.sort()
                _sg[_gk] = ([e[0] for e in _ents], [e[2] for e in _ents])

        for v in self._active_vehicles:
            if v.state != VehicleState.driving:
                continue

            # Current tile speed limit — clamp col/row to world bounds
            col = max(0, min(int(v.position[0]), self._world.cols - 1))
            row = max(0, min(int(v.position[1]), self._world.rows - 1))
            tile = self._world.get_tile(col, row)
            desired_speed = tile.speed_limit * MOVEMENT_SCALE * v.speed_multiplier
            v.desired_speed = desired_speed

            path = v.path
            idx  = v.path_index
            vdx, vdy = _dirs[id(v)]

            # Cardinal group key and projected position for this vehicle
            if abs(vdx) >= abs(vdy):
                gk = (1, 0) if vdx >= 0 else (-1, 0)
            else:
                gk = (0, 1) if vdy >= 0 else (0, -1)
            v_proj = v.position[0] * gk[0] + v.position[1] * gk[1]

            # Gap scan — binary-search for vehicles strictly ahead in the same
            # cardinal group, then apply the three direction/position/lane filters
            # to the nearest _GAP_SCAN_K candidates:
            #   1. moving in the same direction  (dir dot > 0.5, ~60° threshold)
            #      → ignores oncoming traffic and cross-traffic
            #   2. physically ahead of v         (gap projected onto direction > 0)
            #   3. in the same lane/road         (perpendicular offset < 0.5 tiles)
            #      → ignores vehicles on parallel adjacent roads
            target_speed = desired_speed
            closest_gap  = float("inf")

            if gk in _sg:
                _projs, _vehs = _sg[gk]
                _start = bisect.bisect_right(_projs, v_proj)
                for _ki in range(_start, min(_start + _GAP_SCAN_K, len(_projs))):
                    other_v = _vehs[_ki]
                    if other_v is v:
                        continue

                    odx, ody = _dirs[id(other_v)]

                    # 1. Direction alignment
                    if vdx * odx + vdy * ody < 0.5:
                        continue

                    gap_x = other_v.position[0] - v.position[0]
                    gap_y = other_v.position[1] - v.position[1]

                    # 2. Must be physically ahead
                    if gap_x * vdx + gap_y * vdy <= 0.0:
                        continue

                    # 3. Must be in the same lane — cross-product gives lateral offset
                    if abs(gap_x * (-vdy) + gap_y * vdx) > 0.5:
                        continue

                    dist = math.sqrt(gap_x * gap_x + gap_y * gap_y)
                    if dist < closest_gap:
                        closest_gap = dist
                        if closest_gap <= VEHICLE_MIN_GAP:
                            break

            # --- Arc commitment check ---
            # Once a vehicle crosses a turn waypoint and is still within 0.5 tiles
            # past it, gap-following and corner braking are suppressed so the car
            # completes the arc without stopping mid-intersection.  Traffic signals
            # and stop signs still apply; Rule 2 only prevents brake-lock in the box.
            _in_arc = False
            if idx >= 1 and idx + 1 < len(path):
                _arc_corner = path[idx]
                _dist_past = math.sqrt(
                    (v.position[0] - _arc_corner[0]) ** 2 +
                    (v.position[1] - _arc_corner[1]) ** 2
                )
                if _dist_past < 0.5:
                    _in_d  = (path[idx][0] - path[idx - 1][0], path[idx][1] - path[idx - 1][1])
                    _out_d = (path[idx + 1][0] - path[idx][0],  path[idx + 1][1] - path[idx][1])
                    if _in_d != _out_d:
                        _in_arc = True

            # --- Speed decision ---

            if not _in_arc:
                # A. Gap-based following — three-zone braking for visible cascade.
                if closest_gap < VEHICLE_MIN_GAP:
                    target_speed = 0.0
                elif closest_gap < VEHICLE_MIN_GAP * 1.5:
                    target_speed = desired_speed * 0.15
                elif closest_gap < v.following_distance:
                    denom = v.following_distance - (VEHICLE_MIN_GAP * 1.5)
                    if denom > 0:
                        gap_frac = (closest_gap - VEHICLE_MIN_GAP * 1.5) / denom
                        gap_frac = gap_frac ** 0.7
                    else:
                        gap_frac = 1.0
                    target_speed = desired_speed * max(0.15, min(1.0, gap_frac))

                # A2. Corner exit check — look around upcoming turns so vehicles yield
                # when the exit segment is occupied.  The main gap-scan is blind to
                # cross-direction traffic; without this a turning vehicle would drive
                # straight into a queue on the perpendicular road.
                #
                # The nearest exit vehicle is treated as a *virtual leader* at distance
                # (_dtc + _exit_gap) — the total path-length around the corner to that
                # car.  The same three-zone braking curve is applied, combined with min()
                # so it only tightens what the main scan already set.
                if idx + 2 < len(path):
                    _c1x = path[idx + 1][0] - path[idx][0]
                    _c1y = path[idx + 1][1] - path[idx][1]
                    _c2x = path[idx + 2][0] - path[idx + 1][0]
                    _c2y = path[idx + 2][1] - path[idx + 1][1]
                    if (_c1x, _c1y) != (_c2x, _c2y):
                        _cn  = path[idx + 1]
                        _dtc = math.sqrt(
                            (_cn[0] - v.position[0]) ** 2 +
                            (_cn[1] - v.position[1]) ** 2
                        )
                        if _dtc < v.following_distance:
                            if abs(_c2x) >= abs(_c2y):
                                _egk = (1, 0) if _c2x >= 0 else (-1, 0)
                            else:
                                _egk = (0, 1) if _c2y >= 0 else (0, -1)

                            _exit_gap = float("inf")
                            if _egk in _sg:
                                _ep, _ev = _sg[_egk]
                                _cn_proj = _cn[0] * _egk[0] + _cn[1] * _egk[1]
                                _es = bisect.bisect_left(_ep, _cn_proj - 0.1)
                                for _ki in range(_es, min(_es + _GAP_SCAN_K, len(_ep))):
                                    _ov = _ev[_ki]
                                    if _ov is v:
                                        continue
                                    _ogx = _ov.position[0] - _cn[0]
                                    _ogy = _ov.position[1] - _cn[1]
                                    if _ogx * _egk[0] + _ogy * _egk[1] < -0.1:
                                        continue
                                    if abs(_ogx * (-_egk[1]) + _ogy * _egk[0]) > 0.5:
                                        continue
                                    _d = math.sqrt(_ogx * _ogx + _ogy * _ogy)
                                    if _d < _exit_gap:
                                        _exit_gap = _d
                                        if _exit_gap <= VEHICLE_MIN_GAP:
                                            break

                            if _exit_gap < v.following_distance:
                                _eff_gap = _dtc + _exit_gap
                                if _eff_gap < VEHICLE_MIN_GAP:
                                    target_speed = 0.0
                                elif _eff_gap < VEHICLE_MIN_GAP * 1.5:
                                    target_speed = min(target_speed, desired_speed * 0.15)
                                elif _eff_gap < v.following_distance:
                                    _denom = v.following_distance - (VEHICLE_MIN_GAP * 1.5)
                                    _gf = ((_eff_gap - VEHICLE_MIN_GAP * 1.5) / _denom) if _denom > 0 else 1.0
                                    _gf = _gf ** 0.7
                                    target_speed = min(target_speed, desired_speed * max(0.15, min(1.0, _gf)))

                # B. Corner deceleration — archetype-specific apex speed fraction.
                # Conservative drivers crawl through corners; reckless barely slow.
                if idx + 2 < len(path):
                    curr_dx = path[idx + 1][0] - path[idx][0]
                    curr_dy = path[idx + 1][1] - path[idx][1]
                    next_dx = path[idx + 2][0] - path[idx + 1][0]
                    next_dy = path[idx + 2][1] - path[idx + 1][1]
                    if curr_dx != next_dx or curr_dy != next_dy:
                        corner = path[idx + 1]
                        corner_dist = math.sqrt(
                            (corner[0] - v.position[0]) ** 2 +
                            (corner[1] - v.position[1]) ** 2
                        )
                        if corner_dist < CORNER_DECEL_DISTANCE:
                            arch_corner_frac = ARCHETYPE_CONFIGS[v.archetype].get(
                                "corner_fraction", CORNER_SPEED_FRACTION
                            )
                            t_frac = corner_dist / CORNER_DECEL_DISTANCE
                            corner_target = desired_speed * (
                                arch_corner_frac + t_frac * (1.0 - arch_corner_frac)
                            )
                            target_speed = min(target_speed, corner_target)

            # C. Traffic light: simple global phase — H traffic green first half,
            #    V traffic green second half of each cycle.
            if tile.traffic_control == TrafficControl.traffic_light:
                cycle_pos = self._tick % TRAFFIC_LIGHT_CYCLE
                h_green = cycle_pos < TRAFFIC_LIGHT_GREEN_TICKS
                is_green = h_green if abs(vdx) >= abs(vdy) else not h_green
                if not is_green:
                    target_speed = 0.0

            # D. Stop sign: full stop for STOP_SIGN_WAIT_TICKS ticks, then proceed.
            if tile.traffic_control == TrafficControl.stop_sign:
                vid       = id(v)
                tile_pos  = (col, row)
                if tile_pos not in self._stop_served.get(vid, set()):
                    if vid not in self._stop_wait:
                        self._stop_wait[vid] = STOP_SIGN_WAIT_TICKS
                    remaining = self._stop_wait[vid]
                    if remaining > 0:
                        target_speed = 0.0
                        self._stop_wait[vid] -= 1
                    else:
                        self._stop_served.setdefault(vid, set()).add(tile_pos)
                        del self._stop_wait[vid]

            # --- Speed noise — micro-jitter so drivers don't convoy lock-step ---
            # Applied only when the vehicle is free-flowing (no blocker within
            # following_distance and not at a control) so noise doesn't fight braking.
            arch_cfg   = ARCHETYPE_CONFIGS[v.archetype]
            noise_frac = arch_cfg.get("speed_noise", 0.04)
            if target_speed >= desired_speed * 0.9 and closest_gap > v.following_distance:
                jitter = random.uniform(-noise_frac, noise_frac) * desired_speed
                target_speed = max(0.0, target_speed + jitter)

            # --- Smooth accel / decel with archetype-specific rates ---
            accel_mult  = arch_cfg.get("accel_mult", 1.0)
            decel_mult  = arch_cfg.get("decel_mult", 1.0)
            current     = v.current_speed
            if target_speed > current:
                max_delta = (desired_speed * _ACCEL_RATE * accel_mult) if desired_speed > 0 else _ACCEL_RATE
                new_speed = min(target_speed, current + max_delta)
            else:
                max_delta = (desired_speed * _DECEL_RATE * decel_mult) if desired_speed > 0 else _DECEL_RATE
                new_speed = max(target_speed, current - max_delta)

            v.current_speed = max(0.0, new_speed)

            # Advance position along path — sub-tick traversal.
            # Consume the full speed budget across waypoints in one tick so
            # vehicles never overshoot and oscillate backward around a waypoint.
            budget = v.current_speed
            while budget > 1e-9 and idx + 1 < len(path):
                target = path[idx + 1]
                tdx = target[0] - v.position[0]
                tdy = target[1] - v.position[1]
                dist = math.sqrt(tdx * tdx + tdy * tdy)
                if dist <= 1e-9:
                    # Already on the waypoint; advance index without moving.
                    v.path_index += 1
                    idx = v.path_index
                    if idx >= len(path) - 1:
                        v.state = VehicleState.arrived
                        break
                    continue
                if budget >= dist:
                    # Enough budget to reach this waypoint; carry remainder forward.
                    budget -= dist
                    v.position = (float(target[0]), float(target[1]))
                    v.path_index += 1
                    idx = v.path_index
                    if idx >= len(path) - 1:
                        v.state = VehicleState.arrived
                        break
                else:
                    # Budget runs out partway — interpolate along segment.
                    frac = budget / dist
                    v.position = (
                        v.position[0] + tdx * frac,
                        v.position[1] + tdy * frac,
                    )
                    budget = 0

        # Phase 3 — Spawning state transition
        for v in self._active_vehicles:
            if v.state == VehicleState.spawning:
                v.state = VehicleState.driving

        # Phase 4 — Arrival
        arrived = [v for v in self._active_vehicles if v.state == VehicleState.arrived]
        for v in arrived:
            trip_duration = self._tick - v.spawn_tick
            self._completed_trip_ticks.append(trip_duration)
            self._total_trips_completed += 1
            self._trips_this_interval += 1
            vid = id(v)
            self._stop_wait.pop(vid, None)
            self._stop_served.pop(vid, None)
        self._active_vehicles = [v for v in self._active_vehicles if v.state != VehicleState.arrived]

        # Phase 5 — Tile live data
        for row in range(self._world.rows):
            for col in range(self._world.cols):
                t = self._world.get_tile(col, row)
                t.car_count = 0
                t.car_speed = 0.0
        for v in self._active_vehicles:
            if v.state == VehicleState.driving:
                col = int(v.position[0])
                row = int(v.position[1])
                t = self._world.get_tile(col, row)
                t.car_count += 1
                t.car_speed = (
                    t.car_speed * (t.car_count - 1) + v.current_speed
                ) / t.car_count

        # Phase 6 — Metrics
        if self._tick % METRICS_SNAPSHOT_INTERVAL == 0:
            self._metrics_snapshots.append(self._take_snapshot())
            self._trips_this_interval = 0

        self._tick += 1
        if self._tick >= TICKS_PER_DAY:
            self._tick = 0

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def _take_snapshot(self):
        road_tiles = (
            self._world.get_tiles_by_type(TileType.road)
            + self._world.get_tiles_by_type(TileType.highway)
        )
        active_tiles = [t for t in road_tiles if t.speed_limit > 0 and t.car_count > 0]

        if active_tiles:
            # car_speed is in tiles/tick; max speed for a tile = speed_limit * MOVEMENT_SCALE.
            # Dividing by the raw speed_limit integer produces a near-zero ratio even at
            # full speed — the MOVEMENT_SCALE factor corrects the unit mismatch.
            speed_ratios = [
                min(1.0, t.car_speed / (t.speed_limit * MOVEMENT_SCALE))
                for t in active_tiles
            ]
            average_speed_ratio = sum(speed_ratios) / len(speed_ratios)
            congestion_index    = (1.0 - average_speed_ratio) * 100.0
        else:
            congestion_index    = 0.0
            average_speed_ratio = 0.0

        average_travel_time = (
            sum(self._completed_trip_ticks) / len(self._completed_trip_ticks)
            if self._completed_trip_ticks
            else 0.0
        )

        # Throughput as share of vehicles resolved this interval (completed / total in window).
        # Avoids the near-zero score produced by dividing by a fixed tick count on a small map.
        vehicles_in_window = len(self._active_vehicles) + self._trips_this_interval
        throughput_rate = min(1.0, self._trips_this_interval / max(1, vehicles_in_window))

        inverse_congestion = 1.0 - (congestion_index / 100)
        city_health_score = max(
            0.0,
            min(
                100.0,
                (throughput_rate * 0.4 + average_speed_ratio * 0.35 + inverse_congestion * 0.25)
                * 100,
            ),
        )

        congested = []
        for t in road_tiles:
            if t.speed_limit > 0 and t.car_count > 0:
                ratio = 1.0 - min(1.0, t.car_speed / (t.speed_limit * MOVEMENT_SCALE))
                congested.append((t.position[0], t.position[1], ratio))
        congested.sort(key=lambda x: x[2], reverse=True)

        return {
            "tick": self._tick,
            "total_trips_completed": self._total_trips_completed,
            "trips_this_interval": self._trips_this_interval,
            "active_vehicles": len(self._active_vehicles),
            "total_spawned": self._total_spawned,
            "average_travel_time": average_travel_time,
            "congestion_index": congestion_index,
            "average_speed_ratio": average_speed_ratio,
            "city_health_score": city_health_score,
            "top_congested_tiles": congested[:5],
        }
