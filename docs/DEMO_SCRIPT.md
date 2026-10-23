# Demo Script (≈5–7 minutes)

## Setup (before recording)

```bash
cd backend && source .venv/bin/activate
uvicorn app.main:app --port 8000
# other terminal
cd frontend && npm run dev
```

Open `http://127.0.0.1:5173`. Confirm the yellow **DEMO MODE** banner.

## Script

1. **Intro (30s)**  
   “ReturnRight AI is an Alexa+ track demo. It uses a self-hosted MCP server with Streamable HTTP and a web app that is a real MCP client. All purchases and policies are synthetic.”

2. **Connect (30s)**  
   Click **Connect MCP**. Show the tool log: `initialize+tools/list`. Mention protocol negotiation.

3. **Search (45s)**  
   Search `kettle`. Select **NW-1001**. Point out `data_provenance: demo`.

4. **Policy evidence (60s)**  
   Issue type `unwanted`, description “Unused gift”. Run `evaluate_policy`. Show outcome `return_eligible` and cited rule excerpt — “we never invent policy text.”

5. **Case + confirmation (90s)**  
   `create_case` → `prepare_resolution_action` → read the warning → confirm. Highlight `submission_status: demo_only` and audit event `action_confirmed_demo`.

6. **Persistence (45s)**  
   Refresh the page. Workflow resumes from sessionStorage; reopen case events from SQLite.

7. **Failure isolation (45s)**  
   Click `simulate_failure`. Show status unchanged and failure audit event.

8. **Honesty close (30s)**  
   “No private Alexa+ partner APIs, no Amazon account access, no real retailer submission.”

## Optional curl checks

```bash
curl -s http://127.0.0.1:8000/health | jq
curl -s 'http://127.0.0.1:8000/api/v1/orders/search?q=kettle' -H 'X-User-Id: demo-user-1' | jq
```
