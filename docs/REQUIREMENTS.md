# ReturnRight AI — Requirements (MVP)

**Product:** Consumer resolution assistant for returns, warranties, and purchase problems  
**Track:** Amazon Developer Hackathon 2026 — Alexa+  
**Mode:** Synthetic demo data only (no real Amazon / retailer account access)

## Goal

Help a user find a purchase, evaluate documented merchant policies, understand eligibility with evidence, prepare a resolution request, confirm before consequential actions, and resume cases later — via a real MCP server and a web app that is an actual MCP client.

## In scope (MVP)

1. Browse and search sample purchases (product, order ID, merchant).
2. Report defective / unwanted items against a matching order.
3. Retrieve applicable `MerchantPolicy` / `PolicyRule` records and evaluate eligibility outcomes:
   - return eligible
   - warranty guidance
   - insufficient information
   - ineligible
4. Show reasons and policy evidence (rule IDs + excerpts from stored policy text only).
5. Create and update `ResolutionCase` records with event history and follow-up tasks / deadlines.
6. Prepare a resolution request draft; require explicit confirmation before commit.
7. Expose the same business logic through REST **and** MCP tools (no duplicated policy logic).
8. Self-hosted MCP server using the official Python SDK, Streamable HTTP, protocol ≥ 2025-11-25.
9. Polished web UI acting as an MCP client with multi-step workflows and persistent context.
10. Demo mode visually obvious; failure simulation that does not corrupt case state.
11. Setup docs, architecture, tests, demo script, honest developer-tool feedback.

## Out of scope (MVP)

- Real Alexa+ partner APIs or private Amazon tooling
- Real retailer submission / refunds / account login
- Multi-tenant production auth (SSO, OAuth)
- Microservices / message queues
- Production-grade observability SaaS

## Non-negotiable trust rules

- Never invent orders, policies, deadlines, refunds, or submission confirmations.
- Label verified vs demo vs estimate data in API and UI.
- Treat order descriptions and free-text issues as untrusted input (not instructions).
- Never claim a real retailer request succeeded without an authorized integration confirmation.
- Require explicit user approval before consequential actions.

## Acceptance criteria (observable)

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC-001 | Given seeded demo data, search by product/order/merchant returns only matching owned orders | API + MCP protocol tests |
| AC-002 | Policy evaluation cites stored rule IDs/excerpts and never invents terms | Unit + integration tests |
| AC-003 | Consequential action without confirmation token is rejected; with valid token creates audited action marked demo | Integration tests |
| AC-004 | MCP `initialize`, `tools/list`, and `tools/call` succeed over Streamable HTTP | MCP protocol tests |
| AC-005 | Web app completes a multi-step workflow and resumes a saved case after reload | Frontend + manual demo |
| AC-006 | Simulated failure leaves case state unchanged and records a failed audit event | Integration tests |
| AC-007 | Demo banner / `data_provenance: demo` visible in UI and API responses | Manual + schema asserts |
