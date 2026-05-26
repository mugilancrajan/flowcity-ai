# FlowCity AI — Project Context Document

This document is the single source of truth for project decisions, architecture, and current status. Paste this into any new conversation or Claude Code session to restore full context instantly.

Last updated: May 2025

---

## Project Summary

FlowCity AI is a grid-based urban traffic simulation and optimization platform built in Python. A small city is modeled as a grid where vehicle agents travel between residential, commercial, and workplace zones. The system simulates realistic traffic behavior, collects performance metrics, tests interventions, and will eventually use an AI planning layer to recommend improvements.

**Author:** Georgia Tech incoming Industrial Engineering student
**Portfolio goals:** Demonstrate systems thinking, agent-based simulation, graph algorithms, metrics engineering, experiment design, and responsible AI usage
**Target completion:** August 2025

---

## Tech Stack

- Python 3.12
- Pygame — visualization and map editor
- NetworkX — road network graph and pathfinding (DiGraph)
- pandas — metrics collection and analysis
- matplotlib — charts
- JSON — map save/load format

---

## Project Structure

    flowcity-ai/
    ├── src/
    │   ├── world/          # Grid, tiles, map storage
    │   ├── graph/          # NetworkX road network, pathfinding
    │   ├── vehicle/        # Car agent logic
    │   ├── simulation/     # Tick engine
    │   ├── rules/          # Traffic lights, stop signs, right-of-way
    │   ├── metrics/        # Data collection and snapshots
    │   ├── scenarios/      # Events: rush hour, construction, weather
    │   ├── optimizer/      # Experiment and comparison framework
    │   ├── ai_planner/     # LLM analyst layer (Phase 5)
    │   └── visualizer/     # Pygame rendering only — reads state, draws it
    ├── maps/               # Saved city map files (JSON)
    ├── data/               # Simulation run outputs
    ├── docs/               # All documentation
    └── tests/              # Unit tests

Each src/ subfolder has an __init__.py making it an importable Python package.

---

## Architecture Principles

1. Simulation core must be runnable with no Pygame window — headless mode for testing and AI planner
2. Visualizer only reads simulation state — it never modifies it
3. Two application modes share one Pygame window: EDIT mode and SIMULATE mode
4. Tile coordinates are the source of truth — renderer converts to pixels at draw time
5. Derived data is never stored — congestion is calculated from car_speed / speed_limit on demand
6. Every module has a single clear responsibility — no module reaches into another's internals

---

## Phase Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | MVP: grid, agents, routing, basic visualization | In progress |
| 2 | Traffic rules: lights, stop signs, congestion | Not started |
| 3 | Realism: driver variation, speed limits, save/load | Not started |
| 4 | Scenarios: construction, weather, rush hour | Not started |
| 5 | AI Planner: bottleneck analysis, recommendations | Not started |

---

## Approved Data Structures

### Tile

    Tile
    ├── FIXED (saved to map file)
    │   ├── tile_type: enum — empty, road, highway, residential, commercial, workplace
    │   ├── traffic_control: enum — none, stop_sign, traffic_light
    │   ├── speed_limit: int — units in tiles/tick, default by type
    │   ├── position: tuple (col, row) — tile coordinate space, integers
    │   └── capacity: int — spawn/receive volume for destination tiles
    │
    └── LIVE (runtime only, resets each simulation)
        ├── car_count: int — number of cars currently on this tile
        └── car_speed: float — average speed of cars on this tile

Congestion is derived: car_speed / speed_limit. Never stored.

### Tile Default Values

Speed limits by tile type (units: tiles per tick):
- empty: 0
- road: 3
- highway: 6
- residential: 1
- commercial: 2
- workplace: 2

Capacity defaults:
- residential, commercial, workplace: 10
- road, highway, empty: 0

### Vehicle

    Vehicle
    ├── IDENTITY
    │   ├── id: int — unique identifier
    │   ├── origin: tuple (col, row) — spawn tile
    │   └── destination: tuple (col, row) — target tile
    │
    ├── NAVIGATION
    │   ├── path: list of (col, row) tuples — full route from origin to destination
    │   └── path_index: int — current position in path list
    │
    ├── POSITION
    │   └── position: tuple (float, float) — float tile coordinates for smooth movement
    │
    ├── PERSONALITY (set at spawn, fixed for vehicle lifetime)
    │   ├── archetype: enum — conservative, normal, aggressive, reckless
    │   ├── speed_multiplier: float — desired speed as fraction of speed limit
    │   └── following_distance: float — preferred gap to car ahead in tiles
    │
    ├── MOVEMENT (live, changes every tick)
    │   ├── desired_speed: float — speed_limit * speed_multiplier
    │   └── current_speed: float — actual speed this tick
    │
    └── STATE
        └── state: enum — spawning, driving, waiting_light, waiting_stop, arrived

### MetricsSnapshot

    MetricsSnapshot
    ├── TIMESTAMP
    │   └── tick: int — simulation tick when snapshot was taken
    │
    ├── THROUGHPUT
    │   ├── total_trips_completed: int — cumulative since simulation start
    │   └── trips_this_interval: int — completed since last snapshot
    │
    ├── NETWORK HEALTH
    │   ├── congestion_index: float 0-100 — normalized city-wide congestion
    │   ├── average_travel_time: float — mean trip duration in ticks
    │   ├── average_speed_ratio: float — mean car_speed / speed_limit across roads
    │   └── city_health_score: float 0-100 — weighted composite metric
    │
    ├── SIMULATION HEALTH
    │   ├── active_vehicles: int — currently on the network
    │   └── total_spawned: int — cumulative vehicles created
    │
    └── BOTTLENECK DATA
        └── top_congested_tiles: list of (col, row, congestion_ratio) — worst 5 tiles

Snapshot frequency: every N ticks, N configurable, default 10.

City health score formula: throughput_rate * 0.4 + average_speed_ratio * 0.35 + inverse_congestion * 0.25. Weights are tunable.

### Road Network Graph

    NetworkX DiGraph

    NODES
    └── Every tile with type road, highway, residential, commercial, workplace
        └── Node ID: (col, row) tuple matching tile coordinates
        └── Node attributes: tile_type, speed_limit, traffic_control

    EDGES
    └── Connect every adjacent traversable tile pair
        └── Both directions added for normal roads
        └── Edge weight MVP: 1 per connection (distance routing)
        └── Edge weight Phase 3: congestion_factor * distance
        └── One-way Phase 4: remove one directional edge

    INTERSECTIONS
    └── Emerge naturally where 3+ edges meet at a node
        └── Traffic control logic triggered by node traffic_control attribute

    DESTINATION CONNECTIONS
    └── Edges from destination tiles to adjacent road tiles encode facing direction

---

## Key Decisions Summary

| # | Decision |
|---|----------|
| 001 | Visualization-first — Pygame from day one |
| 002 | Tick-based simulation time, not real-time |
| 003 | Python 3.12 for ecosystem stability |
| 004 | Shortest path MVP, congestion-weighted routing Phase 3 |
| 005 | Edit and simulate modes share one Pygame window |
| 006 | Tile coordinates source of truth, renderer converts to pixels |
| 007 | Highway is distinct tile type for future extensibility |
| 008 | Congestion derived from car_speed / speed_limit, never stored |
| 009 | Driver personality as archetypes with internal variance |
| 010 | desired_speed and current_speed are separate vehicle properties |
| 011 | Metrics snapshots every N ticks, live values calculated every tick |
| 012 | City health score as weighted composite metric |
| 013 | DiGraph with every tile as a node, edges connect adjacent tiles |
| 014 | Lane modeling deferred to Phase 4 |
| 015 | Turn penalties deferred, node-level if implemented |
| 016 | Destination facing encoded by graph edges, no explicit property |

Full rationale for each decision in docs/DECISIONS.md.

---

## Current Status

Planning and data structure design complete. Documentation written.
Repository scaffolded. Virtual environment configured with Python 3.12.

### Completed Modules
- src/world/tile.py — Tile class with TileType and TrafficControl enums,
  fixed and live properties, congestion derived property, reset_live_data,
  to_dict, from_dict. Default speed limits confirmed: empty=0, road=3,
  highway=6, residential=1, commercial=2, workplace=2. 32/32 tests passed.

### In Progress
- Phase 1 MVP — World grid next

### Next Step
Implement World grid in src/world/world.py