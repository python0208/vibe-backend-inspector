# Vibe Backend Inspector

Vibe Backend Inspector is a local dashboard and agent for inspecting backend projects created during AI-assisted development.

Current stage: Phase 8.

## Implemented

- FastAPI backend with `/health`.
- React + Vite + TypeScript frontend.
- Frontend health check against the backend.
- Project configuration CRUD.
- Local SQLite storage for tool state.
- OpenAPI URL connection test.
- Database connection test for SQLite, MySQL, and PostgreSQL.
- OpenAPI endpoint discovery and endpoint map.
- SQLite, MySQL, and PostgreSQL database schema introspection and database map.
- Single endpoint test runner with real HTTP execution.
- Database snapshot comparison before and after a single endpoint test through the shared database adapter layer.
- LLM configuration for AI-assisted API testing with OpenAI-compatible and mock providers.
- AI Smart Test plans in Test Runner with semi-automatic step execution and result analysis.
- Test run history stored in the tool's local SQLite database.
- Acceptance reports generated from real endpoint state, test runs, database changes, and AI smart test results.
- Markdown report export.
- Prototype-aligned dashboard layout with Sidebar, TopHeader, cards, and bilingual Chinese / English UI.

## Not Implemented Yet

- Batch API test runner.
- File watcher.
- PDF report export.
- Cloud sharing or team collaboration.

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

When a project has a SQLite, MySQL, or PostgreSQL database configured, each single endpoint test captures a read-only database snapshot before and after the HTTP request through the shared database adapter layer. The Test Runner stores and displays table additions/removals, row count changes, schema changes, and sample row changes.

If no database is configured, or the database snapshot fails, the HTTP test still runs. The snapshot status is stored in `db_changes` on each test run.

## Phase 7 AI Smart Testing

The Settings page can store local LLM configurations for AI-assisted API testing. The first implementation supports OpenAI-compatible chat completion APIs through `base_url`, `api_key`, and `model_name`, plus a built-in `mock` provider for local demos without a real API key.

Security note: API keys are currently stored in the tool's local SQLite database for local development use only. API keys are masked in normal API responses and should not be used for production deployment until encrypted storage or an OS keychain integration is added.

In Test Runner, select an endpoint and an enabled model, then click "Generate AI Test Plan". The model generates structured test steps only. The backend validates the JSON plan before showing it. HTTP execution still goes through the existing Test Runner service, and database change detection still goes through the existing snapshot/db_changes flow. PUT, PATCH, and DELETE steps require confirmation before execution.

Mock mode:

```text
Provider: mock
Base URL: mock://local
Model: mock
API Key: leave empty
```

Use mock mode to verify the UI flow, generated step list, semi-automatic execution, db_changes display, and AI analysis panel without calling an external LLM.

## Phase 8 Acceptance Reports

The Reports page summarizes real evidence already collected by the tool. It reads discovered endpoints, endpoint test status, recent test runs, `db_changes`, and AI Smart Test plans/steps/analysis. It does not execute new tests or modify the inspected backend project.

Report APIs:

```text
GET  /api/projects/{project_id}/reports/summary
GET  /api/projects/{project_id}/reports/latest
POST /api/projects/{project_id}/reports/generate
GET  /api/projects/{project_id}/reports/{report_id}
GET  /api/projects/{project_id}/reports/{report_id}/markdown
```

Open Reports, select a project, run endpoint tests or AI Smart Tests if there is not enough evidence yet, then click "Generate Report". The generated report is saved in the tool's local SQLite database and can be exported as Markdown. PDF export is intentionally not implemented in this phase.

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
