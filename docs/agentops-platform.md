# Niyam AgentOps Platform

Niyam is evolving into a comprehensive **AgentOps Control Plane** for governed autonomous development. This document explains the core concepts of the platform and how they integrate with Niyam's existing modules.

## Core Concepts

### 1. The AgentOps Control Plane
The AgentOps Control Plane is the overarching architecture that manages, observes, and governs AI agents operating within a repository. It provides the necessary infrastructure to transition from unmonitored "vibe coding" to safe, auditable, and production-grade autonomous development. 

The control plane relies on:
- **Policy Enforcement:** Rules defining what agents can and cannot do.
- **Observability:** Complete tracking of agent actions, shell commands, and API calls.
- **Resource Management:** Tracking token consumption, cost, and efficiency.

### 2. Memory Ledger
The **Memory Ledger** is the foundation of agent continuity and auditability. It moves beyond flat markdown files to a structured, append-only log of agent decisions, context, and actions.
- **Lineage:** Tracks why a decision was made and which agent made it.
- **Redaction:** Ensures sensitive data never enters the long-term memory.
- **Context Portability:** Allows an agent to drop into a task and instantly understand the current state without re-reading the entire repository.

### 3. Control Room
The **Control Room** is the operational hub (both CLI and Web UI) for human operators to oversee the AgentOps platform. It allows engineers and managers to:
- Monitor live missions and agent swarms.
- Approve or reject high-risk actions.
- Review evidence reports and readiness scores before merging or deploying.
- Manage the workspace environment dynamically.

## Integration with Current Modules

The AgentOps platform builds upon Niyam's existing capabilities:

- **`memory`**: Currently handles `show`, `add`, and `clear`. The Memory Ledger will extend this module with structured JSONL records, semantic querying, and lineage tracking.
- **`mcp`**: Manages the registry of tools available to agents. The Control Room uses this to gate access to sensitive tools.
- **`guard`**: Provides active execution wrappers. The Control Room visualizes blocked and observed commands logged by `guard`.
- **`mission` & `swarm`**: Orchestrate complex, multi-agent tasks. The Control Room provides the dashboard for monitoring these missions, while the Memory Ledger ensures agents within the swarm share consistent context.
- **`portal`**: The browser-based interface will evolve into the full visual Control Room.
- **`fleet`**: Scales the AgentOps concepts across multiple repositories.
- **`cost` & `evidence`**: Provide the raw metrics and audit reports that populate the Control Room dashboards, proving compliance and tracking FinOps efficiency.
