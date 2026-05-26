# FlowCity AI — Project Charter

**Author:** Mugilan Chinnapparajan
**Started:** May 2025
**Target Completion:** August 2025
**Status:** Phase 1 in progress

---

## Problem Statement

Urban traffic systems are complex. Individual driver decisions create emergent system-level outcomes — congestion, bottlenecks, cascading delays — that are difficult to predict or optimize without simulation. Transportation planners need tools to test interventions before deploying them in the real world.

FlowCity AI is a simplified but behaviorally realistic simulation platform designed to model these dynamics, measure outcomes, and eventually recommend improvements through an AI planning layer.

---

## Project Goals

1. Build a working agent-based traffic simulation on a grid city
2. Collect meaningful metrics that reveal system behavior
3. Create a scenario testing framework for comparing interventions
4. Develop an AI planner that acts as a transportation analyst
5. Produce professional documentation that communicates design decisions clearly

---

## Non-Goals

- This is not a traffic engineering tool for real cities
- This is not a game — entertainment is not the goal
- This does not attempt visual realism — behavior realism is the priority
- This does not model individual driver psychology in clinical detail

---

## Success Criteria

The project is portfolio-ready when it can:
- Simulate a full city day with believable traffic behavior
- Identify and visualize bottlenecks automatically
- Run a baseline vs. intervention comparison and show the difference
- Produce an AI-generated analysis report from real simulation data
- Be explained clearly in a 10-minute technical conversation

---

## Phase Roadmap

| Phase | Focus | Target |
|-------|-------|--------|
| 1 | MVP: grid, agents, routing, basic visualization | June 2025 |
| 2 | Traffic rules: lights, stop signs, congestion | June–July 2025 |
| 3 | Realism: driver variation, speed limits, save/load | July 2025 |
| 4 | Scenarios: construction, weather, rush hour | July–August 2025 |
| 5 | AI Planner: bottleneck analysis, recommendations | August 2025 |

---

## Tech Stack and Rationale

| Tool | Purpose | Why Chosen |
|------|---------|------------|
| Python 3.12 | Core language | Strong ecosystem, IE-relevant |
| Pygame | Visualization | Direct control, integrates with simulation loop |
| NetworkX | Graph and pathfinding | Industry-standard, Dijkstra built-in |
| pandas | Metrics collection | Tabular data, easy analysis |
| matplotlib | Charts | Standard Python visualization |

---

## Learning Objectives

- Graph algorithms and pathfinding in practice
- Agent-based simulation design
- Metrics engineering and experiment design
- Professional repo structure and documentation
- Responsible AI tool usage in engineering workflows

---

## AI Usage Policy

This project uses Claude as a planning partner and coding assistant. See [AI_USAGE.md](AI_USAGE.md) for a detailed log of how AI tools were used and what was learned independently.