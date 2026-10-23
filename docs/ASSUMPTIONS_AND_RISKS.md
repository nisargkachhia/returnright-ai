# Assumptions and Risks

## Assumptions

1. Judges accept synthetic retailers/orders as a valid Alexa+ track demonstration of MCP + agentic UX.
2. “Consequential action” in MVP means committing a **demo** resolution action (label: not submitted to a real retailer).
3. A single demo user (`demo-user-1`) is sufficient for ownership tests; multi-user is optional.
4. Official `mcp` Python SDK ≥ 2.x Streamable HTTP path satisfies the “2025-11-25 or later” requirement via the SDK’s negotiated protocol versions.
5. Browser MCP client via `@modelcontextprotocol/client` + Vite proxy/CORS is acceptable for “web app as MCP client.”
6. SQLite file on a Docker volume is enough for MVP persistence and case resume.
7. Python 3.10–3.14 are supported; CI/docs pin a tested version (3.12 preferred in Docker).

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| MCP SDK / protocol version drift | Broken initialize or browser CORS | Pin `mcp` and client SDK; protocol tests on CI; CORS headers from official docs |
| Accidental “real submission” wording | Trust / judging penalty | Fixed response schemas with `submission_status: demo_only` |
| Duplicated policy logic | Inconsistent outcomes | Single `PolicyService`; REST/MCP thin adapters only |
| Browser cannot talk to MCP | Demo fails | Vite proxy + documented CORS; JSON response mode fallback if needed |
| Case corruption on failures | Unreliable resume | Transactions; `simulate_failure` rolls back; audit of attempted failure |
| Over-scoping Alexa+ claims | Disqualification risk | Explicit “no private Alexa+ tools” in README and UI |

## Open decisions (non-blocking)

- Whether to run MCP on the same port as REST (chosen: same FastAPI process, `/mcp`) vs separate process.
- Whether frontend uses only MCP or MCP+REST for list views (chosen: MCP primary for agentic path; REST for health/seed admin).
