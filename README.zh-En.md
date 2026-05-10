# Vibe Backend Inspector

[简体中文](README.md) | [English](README.zh-En.md)

Vibe Backend Inspector is a local backend inspection and validation workspace for AI-assisted backend development. It can discover APIs through OpenAPI / Swagger, inspect SQLite / MySQL / PostgreSQL database schemas, run real endpoint tests, compare database changes before and after requests, generate AI-assisted API test plans, and create acceptance reports from real evidence.

It is designed for backend projects created or modified with AI coding tools such as Codex, Cursor, Claude Code, OpenCode, Windsurf, Trae, and similar tools.

The goal of this project is not to replace Postman, Swagger, or traditional database clients. Instead, it provides a backend validation workspace specifically for the AI-assisted development workflow:

> When AI writes the backend, this tool helps you see what was actually built.

Current stage: Phase 8.

---

## Core Capabilities

- Project configuration management
- OpenAPI / Swagger endpoint discovery
- API Map for endpoint visualization
- SQLite / MySQL / PostgreSQL connection testing
- SQLite / MySQL / PostgreSQL schema introspection
- Database Map for schema visualization
- Single endpoint testing with real HTTP execution
- Database snapshot comparison before and after endpoint tests
- Database change tracking
- LLM-assisted Smart API Testing
- Test run history
- Acceptance reports generated from real endpoint state, test runs, database changes, and AI Smart Test results
- Markdown report export
- Chinese / English UI switching
- Local-first workflow without requiring cloud deployment

---

## Use Cases

Vibe Backend Inspector is useful when you need to:

- Inspect backend projects generated or modified by AI coding tools
- Check whether AI-generated APIs are actually available and callable
- Help frontend developers understand a backend quickly
- Validate backend projects in teaching, training, or lab environments
- Review outsourced backend deliverables
- Observe database changes caused by endpoint execution
- Let an LLM generate test parameters and test steps from API schemas
- Produce a backend validation report for review or delivery

---

## Implemented

- FastAPI backend with `/health`
- React + Vite + TypeScript frontend
- Frontend health check against the backend
- Project configuration CRUD
- Local SQLite storage for tool state
- OpenAPI URL connection test
- Database connection test for SQLite, MySQL, and PostgreSQL
- OpenAPI endpoint discovery and endpoint map
- SQLite, MySQL, and PostgreSQL database schema introspection and database map
- Single endpoint test runner with real HTTP execution
- Database snapshot comparison before and after a single endpoint test through the shared database adapter layer
- LLM configuration for AI-assisted API testing with OpenAI-compatible and mock providers
- AI Smart Test plans in Test Runner with semi-automatic step execution and result analysis
- Test run history stored in the tool's local SQLite database
- Acceptance reports generated from real endpoint state, test runs, database changes, and AI Smart Test results
- Markdown report export
- Prototype-aligned dashboard layout with Sidebar, TopHeader, cards, and bilingual Chinese / English UI

---

## Not Implemented Yet

- Batch API test runner
- File watcher
- PDF report export
- Cloud sharing or team collaboration
- OpenAPI JSON / YAML file import
- Manual endpoint creation
- Framework source-code route scanning
- Automatic backend code fixing

---

## Overall Workflow

A typical workflow looks like this:

1. Start the backend project you want to inspect.
2. Start the Vibe Backend Inspector backend and frontend.
3. Create a project configuration in Project Setup.
4. Enter the backend service URL.
5. Enter the OpenAPI / Swagger document URL.
6. Enter the database connection information.
7. Sync endpoints in API Map.
8. Inspect database schema in Database Map.
9. Run endpoint tests in Test Runner.
10. Review HTTP responses and database changes.
11. Use AI Smart Testing to generate test plans.
12. Generate an acceptance report in Reports.
13. Export the report as Markdown.

---

## Connecting Your Own Backend Project

Vibe Backend Inspector is not limited to inspecting its own backend. You can use it to inspect your own backend projects, including:

- FastAPI projects
- Django / Django REST Framework projects
- Spring Boot / Java projects
- Go Gin / Echo projects
- NestJS / Express projects
- Laravel / PHP projects
- Any backend project that can expose an OpenAPI / Swagger document

To connect a backend project, you usually need three pieces of information.

### 1. Backend Service URL

Example:

```text
http://localhost:8000
```

or:

```text
http://localhost:8080
```

This URL is used by the tool to execute real HTTP requests.

### 2. OpenAPI / Swagger Document URL

Examples:

```text
http://localhost:8000/openapi.json
http://localhost:8080/v3/api-docs
http://localhost:3000/api-json
http://localhost:8080/swagger/doc.json
```

This URL is used to automatically discover endpoints, build the API Map, and provide endpoint schemas for Test Runner and AI Smart Testing.

### 3. Database Connection Information

Currently supported databases:

- SQLite
- MySQL
- PostgreSQL

The database connection is used by Database Map to inspect schema information and by Test Runner to capture database snapshots before and after endpoint execution.

---

## What Is OpenAPI / Swagger?

OpenAPI is a standard format for describing HTTP APIs. It is usually exposed as a JSON or YAML document.

It describes information such as:

- What endpoints exist in the backend
- The HTTP method of each endpoint, such as GET, POST, PUT, PATCH, DELETE
- The path of each endpoint, such as `/api/users`
- Required path parameters, query parameters, and headers
- Request body schema
- Response schema

Swagger is a set of tools around the OpenAPI ecosystem. Many developers casually refer to an OpenAPI document URL as a Swagger URL.

In this project, OpenAPI / Swagger is used to:

> Automatically discover backend endpoints and power API Map, Test Runner, AI Smart Testing, and Reports.

If your backend project does not provide an OpenAPI / Swagger document, the current version of this tool cannot automatically discover all endpoints.

---

## How Different Backend Frameworks Provide OpenAPI / Swagger

### FastAPI

FastAPI generates OpenAPI by default.

After starting a FastAPI application, the OpenAPI document is usually available at:

```text
http://localhost:8000/openapi.json
```

Swagger UI is usually available at:

```text
http://localhost:8000/docs
```

In Vibe Backend Inspector, use:

```text
Service URL: http://localhost:8000
OpenAPI URL: http://localhost:8000/openapi.json
```

---

### Spring Boot / Java

Spring Boot projects can usually generate OpenAPI documents with `springdoc-openapi`.

Common OpenAPI URL:

```text
http://localhost:8080/v3/api-docs
```

Common Swagger UI URL:

```text
http://localhost:8080/swagger-ui/index.html
```

In Vibe Backend Inspector, use:

```text
Service URL: http://localhost:8080
OpenAPI URL: http://localhost:8080/v3/api-docs
```

---

### Django / Django REST Framework

Django REST Framework does not always generate OpenAPI documents by default. You usually need an extension such as:

- `drf-spectacular`
- `drf-yasg`

After configuration, you may get URLs such as:

```text
http://localhost:8000/schema/
http://localhost:8000/swagger.json
http://localhost:8000/openapi.json
```

In Vibe Backend Inspector, enter the actual OpenAPI JSON URL generated by your Django project.

If your Django project does not have OpenAPI documentation yet, it is recommended to add `drf-spectacular` or `drf-yasg` first.

---

### NestJS

NestJS can generate OpenAPI documents with `@nestjs/swagger`.

A common JSON endpoint may look like:

```text
http://localhost:3000/api-json
```

or another path depending on project configuration.

In Vibe Backend Inspector, use:

```text
Service URL: http://localhost:3000
OpenAPI URL: http://localhost:3000/api-json
```

---

### Go / Gin

Go Gin projects commonly use `swaggo` or `gin-swagger` to generate Swagger documentation.

A common Swagger JSON URL is:

```text
http://localhost:8080/swagger/doc.json
```

In Vibe Backend Inspector, use:

```text
Service URL: http://localhost:8080
OpenAPI URL: http://localhost:8080/swagger/doc.json
```

---

### Express / Node.js

Express projects can use:

- `swagger-jsdoc`
- `swagger-ui-express`

The actual JSON URL depends on project configuration. Examples:

```text
http://localhost:3000/swagger.json
http://localhost:3000/api-docs.json
```

In Vibe Backend Inspector, enter the actual JSON document URL.

---

## What If My Project Does Not Have OpenAPI / Swagger?

The current version mainly relies on OpenAPI / Swagger to automatically discover endpoints.

If your backend project does not have an OpenAPI document, you can use one of the following approaches.

### Recommended: Generate OpenAPI Documentation First

Choose a suitable tool for your stack:

| Stack | Recommended Approach |
|---|---|
| FastAPI | Built-in `/openapi.json` |
| Spring Boot | `springdoc-openapi` |
| Django REST Framework | `drf-spectacular` or `drf-yasg` |
| NestJS | `@nestjs/swagger` |
| Go Gin | `swaggo / gin-swagger` |
| Express | `swagger-jsdoc` and `swagger-ui-express` |

After generating the OpenAPI document, enter the document URL in Project Setup.

### Temporary Option: Use Database Map Only

If your project does not have OpenAPI documentation yet but already has a database, you can still use Database Map:

1. Enter database connection information in Project Setup.
2. Open Database Map.
3. Refresh database schema.
4. Inspect tables, columns, indexes, foreign keys, and sample rows.

However, API Map, Test Runner, and AI Smart Testing will have limited automatic capabilities without endpoint metadata.

### Planned Future Support

Future versions may support more endpoint sources, such as:

- Importing OpenAPI JSON / YAML files
- Manually adding endpoints
- Scanning framework source code for routes
- Discovering endpoints from local proxy traffic

For the current version, OpenAPI / Swagger is the recommended integration path.

---

## Configuring OpenAPI in This Tool

After opening the frontend:

1. Go to Project Setup.
2. Create or select a project.
3. Enter the backend service URL.

```text
Service URL: http://localhost:8000
```

4. Enter the OpenAPI document URL.

```text
OpenAPI URL: http://localhost:8000/openapi.json
```

5. Save the project configuration.
6. Go to API Map.
7. Click Sync OpenAPI.
8. If the configuration is correct, the discovered endpoint list will be displayed.

---

## Configuring Database Connections

Currently supported databases:

- SQLite
- MySQL
- PostgreSQL

### SQLite

Enter the SQLite database file path:

```text
D:\demo\app.db
```

### MySQL

Enter:

```text
Host: localhost
Port: 3306
Database: your_database
Username: root
Password: your_password
```

### PostgreSQL

Enter:

```text
Host: localhost
Port: 5432
Database: your_database
Username: postgres
Password: your_password
```

After configuration, Database Map can display:

- Table list
- Column structure
- Primary keys
- Indexes
- Foreign keys
- Row counts
- Sample rows
- Table relationships

---

## Phase 4: Single Endpoint Test Runner

The Test Runner page can execute one discovered endpoint at a time.

Basic usage:

1. Select a project.
2. Sync OpenAPI from API Map.
3. Open Test Runner.
4. Choose an endpoint.
5. Fill path params, query params, headers, optional Bearer Token, and JSON body.
6. Run the request.

The backend stores each run and exposes:

```text
POST /api/projects/{project_id}/endpoints/{endpoint_id}/test
GET  /api/projects/{project_id}/test-runs
GET  /api/projects/{project_id}/test-runs/{test_run_id}
```

PUT, PATCH, and DELETE requests require frontend confirmation before execution. Sensitive headers are masked in saved and returned test results.

---

## Phase 5: Database Changes

When a project has a SQLite, MySQL, or PostgreSQL database configured, each single endpoint test captures a read-only database snapshot before and after the HTTP request through the shared database adapter layer.

The Test Runner stores and displays:

- Table additions / removals
- Row count changes
- Schema changes
- Sample row changes

If no database is configured, or the database snapshot fails, the HTTP test still runs. The snapshot status is stored in `db_changes` on each test run.

---

## Phase 7: AI Smart Testing

The Settings page can store local LLM configurations for AI-assisted API testing.

The first implementation supports OpenAI-compatible chat completion APIs through `base_url`, `api_key`, and `model_name`, plus a built-in mock provider for local demos without a real API key.

### Security Note

API keys are currently stored in the tool's local SQLite database for local development use only. API keys are masked in normal API responses.

Do not use this storage approach for production deployment until encrypted storage or OS keychain integration is added.

### Mock Mode

If you do not have a real LLM API key, you can use mock mode:

```text
Provider: mock
Base URL: mock://local
Model: mock
API Key: leave empty
```

Mock mode does not call an external model, but it can verify the complete UI flow.

### OpenAI-Compatible Model

If you have access to OpenAI, DeepSeek, Qwen, or another model service compatible with the OpenAI Chat Completion API, configure:

```text
Provider: openai_compatible
Base URL: your model service URL
Model: your model name
API Key: your API key
```

After saving the configuration, open Test Runner:

1. Select an endpoint.
2. Select a model configuration.
3. Click Generate AI Test Plan.
4. Review the generated test steps.
5. Confirm high-risk steps.
6. Execute the test.
7. Review request parameters, response results, database changes, and AI analysis.

The AI only generates test plans and analysis. Real HTTP execution is still performed by the backend Test Runner service.

---

## Phase 8: Acceptance Reports

The Reports page summarizes real evidence already collected by the tool, including:

- Discovered endpoints
- Endpoint test status
- Recent test runs
- `db_changes`
- AI Smart Test plans, steps, and analysis results

Reports does not execute new tests and does not modify the inspected backend project.

Report APIs:

```text
GET  /api/projects/{project_id}/reports/summary
GET  /api/projects/{project_id}/reports/latest
POST /api/projects/{project_id}/reports/generate
GET  /api/projects/{project_id}/reports/{report_id}
GET  /api/projects/{project_id}/reports/{report_id}/markdown
```

Usage:

1. Open Reports.
2. Select a project.
3. If there is not enough evidence yet, run endpoint tests or AI Smart Tests first.
4. Click Generate Report.

The generated report is saved in the tool's local SQLite database and can be exported as Markdown. PDF export is intentionally not implemented in this phase.

---

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

---

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

The UI language can be switched from the top-right language toggle. The selection is stored in browser `localStorage`.

If the backend uses a different address, create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## Windows Scripts

From the repository root:

```bat
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

---

## Tests

Backend:

```bash
cd backend
pytest
```

Frontend build:

```bash
cd frontend
npm run build
```

---

## Security Notes

Phase 5 masks secrets in:

- API responses
- Project configuration
- Saved test run headers
- Database sample diff fields

Fields containing the following keywords are masked:

```text
password
token
secret
credential
```

Local encryption for stored secrets is planned for a later phase.

Use test databases when validating connections and endpoint execution. Avoid connecting directly to production databases.

---

## Recommended Usage Order

For the best experience, use the tool in this order:

1. Make sure the inspected backend project can start normally.
2. Make sure the inspected project exposes OpenAPI / Swagger documentation.
3. Enter the service URL and OpenAPI URL in Project Setup.
4. Sync endpoints in API Map.
5. Configure database connection.
6. Inspect database schema in Database Map.
7. Run key endpoints in Test Runner.
8. Review database changes.
9. Use AI Smart Testing to generate a test plan.
10. Generate an acceptance report in Reports.

---

## Project Positioning

Vibe Backend Inspector is designed for backend validation in the AI-assisted development era.

It focuses on questions such as:

- What endpoints did AI actually create?
- Can the endpoints be called successfully?
- Are request parameters complete?
- Were database tables created correctly?
- Did endpoint execution cause expected database changes?
- Are the API document, real response, and database state consistent?
- Can the collected evidence be turned into an acceptance report?

It is not just an API request tool, and it is not a traditional database client. It is a local inspection and validation workspace built around the AI-assisted backend development process.
