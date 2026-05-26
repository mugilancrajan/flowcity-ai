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
**Trade-off:** Not on the absolute latest Python version, but stability and ecosystem support outweigh that cost.

---

## 004 — Shortest path routing for MVP
**Date:** May 2025
**Decision:** Vehicles will use shortest path (Dijkstra) for MVP routing. Congestion-weighted routing will be added in Phase 3.
**Rationale:** Keeps the MVP scope tight. NetworkX supports both approaches on the same graph — upgrading routing later requires only changing the edge weight used, not rebuilding the graph module.
**Trade-off:** MVP vehicles will not avoid congested roads, which reduces realism. Acceptable at this stage.

---

## 005 — Simulate and edit modes in one Pygame window
**Date:** May 2025
**Decision:** The map editor and simulation view share the same Pygame window with a mode toggle rather than being separate tools or screens.
**Rationale:** Keeps the user experience unified. The user should be able to edit a map, switch to simulation, observe behavior, switch back to edit, make a change, and simulate again — all in one fluid workflow.
**Trade-off:** Requires the application to cleanly manage two distinct states (EDIT mode and SIMULATE mode) from the start.

---

## 006 — Tile coordinate system, not pixel coordinates
**Date:** May 2025
**Decision:** All tiles and vehicles store positions in tile-based coordinates, not pixel coordinates. The renderer converts to pixels at draw time using tile_size as a multiplier.
**Rationale:** Pixel coordinates break when the window resizes. Tile coordinates are resolution-independent — changing tile_size scales the entire world automatically without touching any stored data.
**Implementation note:** Tiles use integer coordinates (col, row). Vehicles use float coordinates (col, row) to express sub-tile positions during smooth movement between tiles.

---

## 007 — Tile type list and highway as distinct type
**Date:** May 2025
**Decision:** Tile types are: empty, road, highway, residential, commercial, workplace. Highway is a separate type from road despite having no unique MVP behavior.
**Rationale:** Designing for extension. Future phases may add highway-specific rules such as no traffic controls, minimum speed limits, on-ramps, and passing lanes. Collapsing highway into road now would require touching every saved map file and the graph builder later. Small cost now, zero refactoring later.
**Future extensions:** Minimum speed enforcement, no traffic control rule, on-ramp and off-ramp connector tiles, lane modeling.

---

## 008 — Congestion as a derived metric, not stored data
**Date:** May 2025
**Decision:** Congestion is calculated on demand as car_speed / speed_limit. It is never stored as a separate field on the Tile.
**Rationale:** Storing derived data creates synchronization problems — three values must be kept consistent every tick instead of two. Calculating congestion from existing live data is always accurate and costs negligible compute.
**Formula:** tile_congestion = car_speed / speed_limit. Range 0.0 (fully stopped) to 1.0 (free flowing). Normalized to 0-100 for display.

---

## 009 — Vehicle personality archetypes with internal variance
**Date:** May 2025
**Decision:** Driver personality is modeled as archetypes (conservative, normal, aggressive, reckless) with randomized variance within each archetype's range rather than purely random personality values.
**Rationale:** Pure random personality produces chaotic, unrealistic distributions. Archetypes with variance produces believable driver populations — a city with defined proportions of driver types feels realistic and is analytically meaningful. Proportions of each archetype are configurable.
**Attributes affected:** speed_multiplier (how far above or below speed limit the driver targets), following_distance (preferred gap to car ahead in tiles).
**Future extensions:** Archetype proportions tunable per scenario, reckless drivers as accident triggers in Phase 4.

---

## 010 — Desired speed vs current speed as separate vehicle properties
**Date:** May 2025
**Decision:** Vehicles store both desired_speed and current_speed as separate properties.
**Rationale:** Desired speed is stable — it is the speed limit multiplied by the driver's personality multiplier, set at spawn. Current speed changes every tick based on traffic conditions, lights, stop signs, and following distance. Conflating them would make it impossible to model deceleration and acceleration correctly.
**Usage:** Tile car_speed averages use current_speed. Congestion calculations use current_speed. Desired speed is the target the vehicle accelerates toward when conditions allow.

---

## 011 — Metrics snapshot frequency decoupled from simulation tick rate
**Date:** May 2025
**Decision:** Live values (car counts, speeds, congestion ratios) are calculated every tick. Full MetricsSnapshots are written to memory every N ticks, where N is configurable with a default of 10.
**Rationale:** Recording a full snapshot every tick would generate enormous amounts of data and slow the simulation. Calculating live values every tick is necessary for the simulation to run correctly. Decoupling storage frequency from calculation frequency gives full simulation accuracy with manageable data volume.
**Trade-off:** Snapshot resolution is lower than tick resolution. At 60 ticks per second with N=10, you get 6 snapshots per second — sufficient for meaningful charts and AI planner analysis.

---

## 012 — City health score as weighted composite metric
**Date:** May 2025
**Decision:** A single city_health_score (0-100) is calculated per snapshot as a weighted composite of throughput rate, average speed ratio, and inverse congestion index.
**Rationale:** The AI planner needs a single comparable number to evaluate whether an intervention improved the city. Individual metrics like congestion or travel time can move in opposite directions — a road closure might reduce congestion but increase travel time. A composite score resolves that ambiguity.
**Initial weights:** throughput_rate * 0.4 + average_speed_ratio * 0.35 + inverse_congestion * 0.25. Weights are tunable and will be refined once real simulation data is available.
**Note:** Weights are an analytical decision, not an engineering one. They represent a value judgment about what makes a city healthy. Document any changes to weights in EXPERIMENTS.md.

---

## 013 — NetworkX DiGraph with every tile as a node
**Date:** May 2025
**Decision:** The road network is modeled as a NetworkX DiGraph where every traversable tile is a node identified by its (col, row) coordinate. Edges connect adjacent traversable tiles in both directions for normal roads.
**Rationale:** Modeling each tile as a node rather than only intersections and destinations allows per-tile congestion weighting in Phase 3. If entire road segments were single edges, varying conditions along the segment could not be represented. Every-tile-as-node also maps cleanly onto the grid coordinate system with no translation layer needed.
**Edge weights (MVP):** 1 per tile-to-tile connection — pure distance routing.
**Edge weights (Phase 3):** congestion_factor * distance — cars naturally avoid congested roads.
**One-way streets (Phase 4):** Implemented by removing one directional edge from a pair. DiGraph supports this natively.
**Intersection detection:** Not a special tile type. Intersections emerge naturally as nodes where 3 or more edges meet. Traffic control logic is triggered by the node's traffic_control attribute.

---

## 014 — Lane modeling deferred to Phase 4
**Date:** May 2025
**Decision:** Lane data will not be modeled in the Tile or graph for MVP or Phase 2. Deferred to Phase 4 at earliest.
**Rationale:** Lane modeling significantly increases complexity in both the data structures and movement logic. The simulation can produce meaningful and realistic behavior without it through Phase 3. Adding it later does not require restructuring existing data — it extends the Tile and edge model.
**Future implementation:** Lane count per direction stored on Tile. Edge capacity derived from lane count. Passing logic added to vehicle movement.

---

## 015 — Turn penalties deferred, not modeled on edges
**Date:** May 2025
**Decision:** Turn penalties will not be applied to edge weights in MVP. If implemented in a future phase, they will be modeled at the node level, not the edge level.
**Rationale:** Turn penalties are a property of transitioning between two edges through a node, not a property of the edge itself. Applying them to edges is architecturally incorrect. NetworkX supports node-level turn penalties but the implementation is complex. Not worth the cost in early phases.
**Future implementation:** Node-level turn cost applied when routing through an intersection based on entry and exit edge directions.

---

## 016 — Destination tile facing encoded by graph edges
**Date:** May 2025
**Decision:** The direction a destination tile faces — meaning which road tiles serve it — is encoded implicitly by the edges connecting it to adjacent road tiles in the graph. No explicit facing property is stored on the Tile.
**Rationale:** The graph already encodes connectivity. A residential tile with one edge pointing south is served by the road to its south. Multiple edges mean multiple access points. This is information the graph provides for free without adding a redundant property to the Tile data structure.
**Future extension:** Edge direction from destination tiles can be used to model designated entry points, parking lot connections, and driveway logic in later phases.