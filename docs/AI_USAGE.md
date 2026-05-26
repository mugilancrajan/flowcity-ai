# AI Usage Log

This document records how AI tools were used during the development of FlowCity AI, what was generated vs. learned independently, and how outputs were validated.

---

## Philosophy

AI tools are used here as a senior engineering mentor and coding assistant — not as a shortcut. Every design decision is understood before implementation. Generated code is read, questioned, and validated before it enters the codebase.

---

## Tools Used

- **Claude (Anthropic)** — planning conversations, architecture design, code generation, debugging assistance
- **Claude Code** — in-editor coding assistant for implementation

---

## Usage Log

### May 2025 — Project Planning
Used Claude to work through project architecture before writing any code. Discussed layer separation, MVP scope, tech stack tradeoffs, and phase roadmap. All major decisions were made collaboratively with reasoning explained — not accepted blindly.

Key things learned through this process:
- Why the simulation core must be separated from the visualization layer
- Why tick-based simulation is preferable to real-time for this use case
- How NetworkX graph edge weights enable future congestion-weighted routing
- Professional repo structure and documentation conventions
- How to scope an MVP tightly without sacrificing architectural integrity

### Ongoing — Code Generation
Claude Code assists with implementation. Workflow:
1. Understand what needs to be built and why (planning conversation first)
2. Describe the requirement to Claude Code with full context
3. Review all generated code line by line before accepting
4. Ask follow-up questions about anything not understood
5. Run and test — never assume generated code is correct

---

## What AI Did Not Do

- Make project decisions unilaterally
- Replace understanding of core concepts — algorithms and patterns are studied independently
- Produce code that was accepted without review and testing