# FlowCity AI

A grid-based urban traffic simulation and optimization platform built in Python.

FlowCity AI models a small city as a road network where vehicle agents travel 
between residential, commercial, and workplace zones. The system simulates 
realistic traffic behavior, collects performance metrics, tests interventions, 
and uses an AI planning layer to recommend improvements.

Built as a portfolio project exploring agent-based simulation, graph algorithms, 
operations research, and applied AI.

---

## Status

🚧 In active development — Phase 1 (MVP) in progress

---

## Features (Planned by Phase)

**Phase 1 — MVP**
- Grid-based city map with zone types
- Road network graph with shortest-path routing
- Vehicle agents that spawn, route, and complete trips
- Basic Pygame visualization
- Core metrics: active vehicles, completed trips, average travel time

**Phase 2 — Traffic Rules**
- Traffic lights and stop signs
- Following distance and car spacing
- Congestion modeling

**Phase 3 — Realism**
- Driver personality variation
- Road speed limits
- Congestion heatmap
- Save/load city maps

**Phase 4 — Scenarios**
- Construction zones, accidents, weather
- Morning/evening rush hour
- Baseline vs. intervention comparisons

**Phase 5 — AI Planner**
- LLM-backed transportation analyst
- Bottleneck identification
- Intervention recommendations
- Executive summary reports

---

## Tech Stack

- Python 3.12
- Pygame — visualization
- NetworkX — road network graph and pathfinding
- pandas — metrics and data collection
- matplotlib — charts and analysis

---

## Project Structure

 - src/          # Simulation source code
 - maps/         # Saved city map files (JSON)
 - data/         # Simulation run outputs
 - docs/         # Architecture and design documentation
 - tests/        # Unit tests

---

## Setup

```bash
git clone https://github.com/mugilancrajan/flowcity-ai.git
cd flowcity-ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Documentation

- [Project Charter](docs/PROJECT_CHARTER.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Design Decisions](docs/DECISIONS.md)
- [AI Usage](docs/AI_USAGE.md)

---

## Author

**Mugilan Chinnapparajan** — Incoming Georgia Tech Industrial Engineering Student
Interests: systems thinking, operations, consulting, engineering management, AI