# MVP Backlog

## P0 — Foundation (must ship)

1. Project scaffold: backend, frontend, Docker, `.env.example`, README
2. SQLite schema + seed for all domain entities
3. Shared services: orders, policy evaluation, cases, confirmation, audit
4. REST health + CRUD-ish read APIs using shared services
5. MCP Streamable HTTP server with real initialize / tools/list / tools/call
6. Web MCP client completing search → evaluate → case → confirm flow
7. Demo mode banner + provenance fields
8. Unit + API integration + MCP protocol tests for P0 paths

## P1 — Resolution polish

1. Follow-up tasks / deadline UI
2. Case resume after reload
3. Failure simulation tool + UI affordance
4. Structured logging + graceful shutdown
5. Demo script + developer-tool feedback doc

## P2 — Stretch

1. Richer policy packs / multiple merchants
2. Export case summary PDF/Markdown
3. Hardened auth beyond demo headers
4. Playwright e2e against Docker stack

## Build order (verifiable steps)

1. Docs (this set) ✓
2. Backend config + DB models + seed → pytest model/seed tests
3. Policy + case services → unit tests
4. REST routers → API integration tests
5. MCP tools mounted on FastAPI → MCP protocol tests
6. Frontend scaffold + MCP client wrapper → vitest for client helpers
7. Workflow UI pages → manual smoke + vitest
8. Docker compose + README + demo script
