# ReturnRight AI — Backend

FastAPI REST API + official MCP Python SDK Streamable HTTP server.

## Supported Python

3.10–3.14 (Docker image uses 3.12).

## Quick start

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
mkdir -p ../data
python -m app.cli
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`python -m app.cli` creates the SQLite schema (version 2) and loads synthetic demo data. Startup also initializes and seeds if the database is empty.

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

- Health: `GET /health`
- REST: `/api/v1/...`
- MCP: `POST http://127.0.0.1:8000/mcp/` (Streamable HTTP)

## Tests

```bash
pytest -q
```
