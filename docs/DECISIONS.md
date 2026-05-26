# Design Decisions Log

A running record of significant technical decisions made during development, including what was considered and why choices were made.

---

## 001 — Visualization-first approach
**Date:** May 2025
**Decision:** Start with Pygame as the primary interface rather than building a headless simulation first.
**Rationale:** Visualization is central to the project's goals. Seeing cars move, pile up, and respond to interventions is core to the educational and portfolio value. A headless-first approach would delay the feedback loop that makes the project meaningful.
**Trade-off:** Slightly more complex early architecture — simulation and renderer must be kept separate from day one.

---

## 002 — Tick-based simulation time
**Date:** May 2025
**Decision:** Use a discrete tick-based time model rather than real-time simulation.
**Rationale:** Tick-based simulation is easier to control, test, pause, speed up, and reason about. It allows the simulation to run faster than real time and makes metrics collection deterministic.
**Trade-off:** Requires deciding what one tick represents in simulated time — will revisit when implementing rush hour timing.

---

## 003 — Python 3.12 over 3.14
**Date:** May 2025
**Decision:** Use Python 3.12 as the project interpreter despite 3.14 being available.
**Rationale:** Pygame and several other dependencies do not yet have pre-built wheels for Python 3.14. 3.12 is the current stable standard for most professional Python projects.

---

## 004 — Shortest path routing for MVP
**Date:** May 2025
**Decision:** Vehicles will use shortest path (Dijkstra) for MVP routing. Congestion-weighted routing will be added in a later phase.
**Rationale:** Keeps the MVP scope tight. NetworkX supports both approaches on the same graph — upgrading routing later requires only changing the edge weight used, not rebuilding the graph module.

---

## 005 — Simulate and edit modes in one Pygame window
**Date:** May 2025
**Decision:** The map editor and simulation view will share the same Pygame window with a mode toggle, rather than being separate tools or screens.
**Rationale:** Keeps the user experience unified. The user should be able to edit a map, switch to simulation, observe behavior, switch back to edit, make a change, and simulate again — all in one fluid workflow.
**Trade-off:** Requires the application to cleanly manage two distinct states (EDIT mode and SIMULATE mode) from the start.