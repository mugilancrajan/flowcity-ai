import math

from src.config import (
    DEFAULT_SPEED, SPEED_SLOW, SPEED_NORMAL, SPEED_FAST, SPEED_ULTRA,
    TICKS_PER_DAY, TICKS_PER_SIMULATED_MINUTE, MOVEMENT_SCALE,
    METRICS_SNAPSHOT_INTERVAL,
)
from src.world.tile import TileType
from src.graph.road_network import RoadNetwork
from src.vehicle.vehicle import VehicleState
from src.vehicle.vehicle_spawner import VehicleSpawner
from src.simulation.spawn_manager import SpawnManager

_VALID_SPEEDS = {SPEED_SLOW, SPEED_NORMAL, SPEED_FAST, SPEED_ULTRA}


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

    def set_speed(self, speed):
        if speed not in _VALID_SPEEDS:
            raise ValueError(f"Invalid speed: {speed!r}. Must be one of {_VALID_SPEEDS}")
        self._speed = speed

    # ------------------------------------------------------------------
    # Simulation step
    # ------------------------------------------------------------------

    def step(self):
        # Phase 1 — Spawn
        vehicle = self._spawn_manager.get_spawn(self._tick, self._next_vehicle_id)
        if vehicle is not None:
            self._active_vehicles.append(vehicle)
            self._next_vehicle_id += 1
            self._total_spawned += 1

        # Phase 2 — Movement
        for v in self._active_vehicles:
            if v.state != VehicleState.driving:
                continue

            col = int(v.position[0])
            row = int(v.position[1])
            tile = self._world.get_tile(col, row)
            desired_speed = tile.speed_limit * MOVEMENT_SCALE * v.speed_multiplier
            v.desired_speed = desired_speed

            # Lookahead: path_index+1 through path_index+1+int(following_distance)
            lookahead_start = v.path_index + 1
            lookahead_end = min(
                v.path_index + 1 + int(v.following_distance),
                len(v.path),
            )
            current_speed = desired_speed
            for i in range(lookahead_start, lookahead_end):
                ahead_pos = v.path[i]
                ahead_tile = self._world.get_tile(ahead_pos[0], ahead_pos[1])
                if ahead_tile.car_count > 0:
                    distance = i - v.path_index
                    current_speed = max(0.0, desired_speed * (distance / v.following_distance))
                    break

            v.current_speed = current_speed

            if v.path_index + 1 < len(v.path):
                target = v.path[v.path_index + 1]
                dx = target[0] - v.position[0]
                dy = target[1] - v.position[1]
                magnitude = math.sqrt(dx * dx + dy * dy)
                if magnitude > 0:
                    direction = (dx / magnitude, dy / magnitude)
                else:
                    direction = (0.0, 0.0)

                new_pos = (
                    v.position[0] + direction[0] * current_speed,
                    v.position[1] + direction[1] * current_speed,
                )
                v.position = new_pos

                dist_to_next = math.sqrt(
                    (new_pos[0] - target[0]) ** 2 + (new_pos[1] - target[1]) ** 2
                )
                if dist_to_next < 0.1:
                    v.position = (float(target[0]), float(target[1]))
                    v.path_index += 1
                    if v.path_index >= len(v.path) - 1:
                        v.state = VehicleState.arrived

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
            congestion_index = (
                sum(1.0 - (t.car_speed / t.speed_limit) for t in active_tiles)
                / len(active_tiles)
                * 100
            )
            average_speed_ratio = (
                sum(t.car_speed / t.speed_limit for t in active_tiles) / len(active_tiles)
            )
        else:
            congestion_index = 0.0
            average_speed_ratio = 0.0

        average_travel_time = (
            sum(self._completed_trip_ticks) / len(self._completed_trip_ticks)
            if self._completed_trip_ticks
            else 0.0
        )

        throughput_rate = min(1.0, self._trips_this_interval / METRICS_SNAPSHOT_INTERVAL)
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
                ratio = 1.0 - (t.car_speed / t.speed_limit)
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
