# Vibe Backend Inspector

Vibe Backend Inspector is a local dashboard and agent for inspecting backend projects created during AI-assisted development.

Current stage: Phase 5.

## Implemented

- FastAPI backend with `/health`.
- React + Vite + TypeScript frontend.
- Frontend health check against the backend.
- Project configuration CRUD.
- Local SQLite storage for tool state.
- OpenAPI URL connection test.
- Basic database connection test for SQLite, MySQL, and PostgreSQL.
- OpenAPI endpoint discovery and endpoint map.
- SQLite database schema introspection and database map.
- Single endpoint test runner with real HTTP execution.
- SQLite database snapshot comparison before and after a single endpoint test.
- Test run history stored in the tool's local SQLite database.
- Prototype-aligned dashboard layout with Sidebar, TopHeader, cards, and bilingual Chinese / English UI.

## Not Implemented Yet

- Batch API test runner.
- File watcher.
- Acceptance reports.
- AI analysis.

## Phase 4 Single Endpoint Test Runner

The Test Runner page can execute one discovered endpoint at a time. Select a project, sync OpenAPI from API Map, open Test Runner, choose an endpoint, fill path params, query params, headers, optional Bearer Token, and JSON body, then run the request.

The backend stores each run and exposes:

```text
POST /api/projects/{project_id}/endpoints/{endpoint_id}/test
GET  /api/projects/{project_id}/test-runs
GET  /api/projects/{project_id}/test-runs/{test_run_id}
```

PUT, PATCH, and DELETE requests require frontend confirmation before execution. Sensitive headers are masked in saved and returned test results.

## Phase 5 Database Changes

When a project has a SQLite database configured, each single endpoint test captures a read-only database snapshot before and after the HTTP request. The Test Runner stores and displays table additions/removals, row count changes, schema changes, and sample row changes.

If no database is configured, or the database snapshot fails, the HTTP test still runs. The snapshot status is stored in `db_changes` on each test run.

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend runs at:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

The UI language can be switched from the top-right language toggle. The selection is stored in browser localStorage.

If the backend uses a different address, create `frontend/.env`:

```text
VITE_API_BASE_URL=http://localhost:8000
```

## Windows Scripts

From the repository root:

```bash
scripts\dev_backend.bat
scripts\dev_frontend.bat
scripts\dev_all.bat
```

PowerShell variants are also available:

```powershell
.\scripts\dev_backend.ps1
.\scripts\dev_frontend.ps1
.\scripts\dev_all.ps1
```

## Tests

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm run build
```

## Security Notes

Phase 5 masks secrets in API responses, project configuration, saved test run headers, and database sample diff fields with names containing password, token, secret, or credential. Local encryption for stored secrets is planned for a later phase. Use test databases when validating connections and endpoint execution.
