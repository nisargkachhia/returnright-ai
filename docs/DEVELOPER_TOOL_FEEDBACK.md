# Developer Tool Feedback (Honest)

Feedback for Amazon Developer Hackathon tooling / Alexa+ MCP expectations from building ReturnRight AI.

## What worked well

1. **Official MCP Python SDK Streamable HTTP** is documentable and testable. `initialize` → `tools/list` → `tools/call` over HTTP is a clear judging surface.
2. **Mounting MCP inside FastAPI** (with host lifespan owning `session_manager.run()`) keeps one deployable process for REST + MCP.
3. **Shared domain services** make it obvious that REST and MCP cannot drift on policy logic — good for trust demos.
4. **Browser MCP clients** via `@modelcontextprotocol/client` + Streamable HTTP are viable when CORS/`Mcp-*` headers are configured carefully.

## Friction

1. **Starlette `Mount` trailing-slash 307s** can drop POST bodies; clients must hit `/mcp/` consistently. Easy to miss in demos.
2. **DNS-rebinding / Host allowlists** on Streamable HTTP are easy to trip when moving off localhost — docs help, but first deploy surprises are likely.
3. **SDK import paths moved** (`MCPServer` location, client package split). Pin versions and lock examples to those pins.
4. **Stateless + JSON response mode** simplifies browser demos but differs from long-lived SSE session mental models; clarify which mode judges expect.
5. **Hackathon “Alexa+” framing** without accessible public partner APIs forces honest synthetic demos — judges should reward protocol correctness and trust UX over fake Amazon integrations.

## Suggestions

1. Publish a minimal “Streamable HTTP + FastAPI mount + browser CORS” golden sample pinned to protocol `2025-11-25+`.
2. Provide a conformance checklist: initialize, tools/list, tools/call, error shape, and “no invented side effects” for consequential tools.
3. Document trailing-slash and proxy requirements for Vite/nginx frontends early in the brief.
4. Encourage demos to label `demo_only` submission statuses explicitly — it improves trust and scoring clarity.

## What we intentionally did not claim

- Access to private Alexa+ partner tools
- Real Amazon customer accounts
- Successful real retailer return submissions
