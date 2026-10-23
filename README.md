# ReturnRight AI

An AI-powered consumer resolution agent that helps people navigate returns, warranties, and purchase issues by checking policies, preparing claims, and tracking follow-ups.

This repository is a **working synthetic demo** for the **Amazon Developer Hackathon 2026 — Alexa+ track**. The web app is a real MCP client. The backend hosts an **official MCP Python SDK** server over **Streamable HTTP**, plus a REST API that shares the same domain services.

## Problem

Return and warranty rules are scattered across merchants. Deadlines are easy to miss, and shoppers often cannot tell whether an item is still eligible or what to say next.

## Solution

ReturnRight AI walks through a resolution: find the purchase, check a stored sample policy, prepare a claim draft, require an explicit confirmation, and keep the case plus follow-ups. The intended product is conversational. The running demo is a guided workflow on labeled sample data.

## Current implementation status

Implemented locally:

- Synthetic purchase search and order detail
- Deterministic policy checks that cite stored sample rules
- Resolution case creation, status, audit events, and follow-ups
- Explicit confirmation before a demo-only action is recorded
- Official Python MCP server on Streamable HTTP, plus a REST API using the same services
- Visible **DEMO MODE** banner

Not implemented:

- Free-form chat or a live voice assistant
- Contacting a merchant, submitting a return, issuing a refund, or verifying a real warranty
- Any private Alexa+ partner integration

## Features

- Search sample orders by product, order number, or merchant
- Evaluate `unwanted`, `change_of_mind`, `defective`, and `malfunction` against labeled policies
- Outcomes: `return_eligible`, `warranty_guidance`, `insufficient_information`, `ineligible`
- Create a case, prepare a draft, and confirm with a one-time token
- Resume workflow context after refresh, and list case events and follow-ups
- Simulate a failure without changing case status

## Technology stack

- Frontend: React, TypeScript, Vite, MCP TypeScript client
- Backend: Python, FastAPI, SQLAlchemy, SQLite
- Agent protocol: official MCP Python SDK, Streamable HTTP
- Tests: pytest and Vitest

## Project media

Concept artwork for the Devpost gallery:

`docs/media/returnright-ai-concept.png`

Caption: Concept artwork for ReturnRight AI. The running demo uses synthetic orders and does not contact merchants.

Submission steps: [docs/DEVPOST_CHECKLIST.md](docs/DEVPOST_CHECKLIST.md). Short narration: [docs/demo-script.md](docs/demo-script.md).

## Quick start (local)

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
mkdir -p ../data
uvicorn app.main:app --reload --port 8000

# Frontend (second terminal)
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173).

- REST health: `GET http://127.0.0.1:8000/health`
- MCP endpoint: `http://127.0.0.1:8000/mcp/` (use trailing slash)

## Docker

```bash
docker compose up --build
```

Web UI: [http://127.0.0.1:8080](http://127.0.0.1:8080)

## What is implemented

| Layer | Details |
|-------|---------|
| Domain | User, Order, OrderItem, MerchantPolicy, PolicyRule, ResolutionCase, ResolutionAction, AuditEvent, FollowUpTask |
| Policy | Single `PolicyService` used by REST and MCP |
| MCP tools | search/get orders, evaluate policy, cases, prepare/confirm actions, simulate failure |
| Trust | Demo banner, `data_provenance`, `submission_status: demo_only`, explicit confirmation |
| Tests | pytest unit + API integration + MCP protocol; Vitest workflow persistence |

## Docs

- [Requirements](docs/REQUIREMENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [MVP backlog](docs/MVP_BACKLOG.md)
- [Assumptions & risks](docs/ASSUMPTIONS_AND_RISKS.md)
- [Demo script](docs/DEMO_SCRIPT.md)
- [Developer tool feedback](docs/DEVELOPER_TOOL_FEEDBACK.md)

## Honest limits

- No private Alexa+ partner tools
- No real Amazon customer accounts
- No real retailer submissions — confirmed actions are **demo_only**

## Config

Copy [`.env.example`](.env.example) to `.env`. No secrets are required for the demo.
