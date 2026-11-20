# ADR 002: Two Separate MCP Servers (Banking vs Compliance)

**Status:** Accepted  
**Date:** 2025-01-20  
**Author:** Karthikeyan Sakthivel

---

## Context

We need to expose banking and compliance capabilities as MCP tools to agents.
Decision: one monolithic MCP server vs two domain-separated servers.

## Decision

Use **two separate MCP servers**: Banking MCP (port 8002) and Compliance MCP (port 8003).

## Rationale

**Domain separation:**
- Banking tools are owned by the Platform Engineering team.
- Compliance tools are owned by the Regulatory & Compliance team.
- Separate servers means separate ownership, deployment, and versioning.

**Security boundary:**
- Compliance MCP (KYC, sanctions, SAR) requires higher security clearance.
- Separating it allows different RBAC policies per server.
- A compromised Banking MCP cannot access compliance data.

**Independent scaling:**
- Compliance checks (sanctions, AML) are heavier and may need more replicas.
- Banking MCP handles high-frequency lightweight calls.

**Contract testing:**
- Each server has its own contract tests (`tests/contract/`).
- Teams can evolve their server independently without breaking the other.

**Tool registry:**
- `tool_registry.py` maps tool names to server URLs.
- Adding a new tool to a server requires one line in `tool_registry.py`.
- Agents never know which server a tool comes from.

## Consequences

- Two Docker services in `docker-compose.yml`.
- Two Kubernetes Deployments in `helm/`.
- Contract tests must pass for both servers before any deployment.
- `MCPClient` is shared — both servers use the same HTTP client.
