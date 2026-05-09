import { AlertTriangle, Clock3, Code2, Play, ShieldCheck, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { listEndpoints } from "../api/endpoints";
import { listTestRuns, runEndpointTest } from "../api/tests";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/ui/StatCard";
import { StatusBadge, type StatusTone } from "../components/ui/StatusBadge";
import type { Messages } from "../i18n";
import type { Endpoint } from "../types/api";
import type { PageKey } from "../types/navigation";
import type { ProjectListItem } from "../types/project";
import type { DbChanges, TestRequestPayload, TestRun } from "../types/tests";

interface KeyValueRow {
  id: string;
  key: string;
  value: string;
}

interface TestRunnerProps {
  t: Messages;
  projects: ProjectListItem[];
  selectedProjectId: number | null;
  initialEndpointId: number | null;
  onNavigate: (page: PageKey) => void;
}

const destructiveMethods = new Set(["DELETE", "PUT", "PATCH"]);

export function TestRunner({
  t,
  projects,
  selectedProjectId,
  initialEndpointId,
  onNavigate
}: TestRunnerProps) {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [selectedEndpointId, setSelectedEndpointId] = useState<number | null>(null);
  const [pathRows, setPathRows] = useState<KeyValueRow[]>([]);
  const [queryRows, setQueryRows] = useState<KeyValueRow[]>([]);
  const [headerRows, setHeaderRows] = useState<KeyValueRow[]>([{ id: createId(), key: "", value: "" }]);
  const [bearerToken, setBearerToken] = useState("");
  const [bodyText, setBodyText] = useState("{}");
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [latestRun, setLatestRun] = useState<TestRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedProject = projects.find((project) => project.id === selectedProjectId) ?? null;
  const selectedEndpoint = endpoints.find((endpoint) => endpoint.id === selectedEndpointId) ?? null;
  const computedUrl = selectedProject && selectedEndpoint
    ? joinUrl(selectedProject.service_base_url, selectedEndpoint.path)
    : "-";
  const passedCount = testRuns.filter((run) => run.status === "passed").length;
  const failedCount = testRuns.filter((run) => run.status === "failed").length;
  const avgResponseTime = useMemo(() => {
    const timings = testRuns
      .map((run) => run.response_time_ms)
      .filter((value): value is number => typeof value === "number");
    if (!timings.length) return "-";
    return `${Math.round(timings.reduce((sum, value) => sum + value, 0) / timings.length)} ms`;
  }, [testRuns]);

  async function refreshData(projectId = selectedProjectId) {
    if (!projectId) {
      setEndpoints([]);
      setTestRuns([]);
      setLatestRun(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [endpointData, runData] = await Promise.all([
        listEndpoints(projectId),
        listTestRuns(projectId)
      ]);
      setEndpoints(endpointData);
      setTestRuns(runData);
      setLatestRun((current) => current ?? runData[0] ?? null);
      setSelectedEndpointId((current) => {
        if (initialEndpointId && endpointData.some((endpoint) => endpoint.id === initialEndpointId)) {
          return initialEndpointId;
        }
        if (current && endpointData.some((endpoint) => endpoint.id === current)) {
          return current;
        }
        return endpointData[0]?.id ?? null;
      });
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.testRunner.loadFailed);
      setEndpoints([]);
      setTestRuns([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshData();
  }, [selectedProjectId, initialEndpointId]);

  useEffect(() => {
    if (!selectedEndpoint) {
      setPathRows([]);
      setQueryRows([]);
      setBodyText("{}");
      return;
    }
    setPathRows(rowsFromParameters(selectedEndpoint.path_params));
    setQueryRows(rowsFromParameters(selectedEndpoint.query_params));
    setBodyText(shouldShowBody(selectedEndpoint.method) ? JSON.stringify(createBodyExample(selectedEndpoint.request_body_schema), null, 2) : "");
  }, [selectedEndpointId, selectedEndpoint]);

  async function runTest() {
    if (!selectedProjectId || !selectedEndpoint) return;
    setError(null);

    if (destructiveMethods.has(selectedEndpoint.method.toUpperCase())) {
      const confirmed = window.confirm(t.testRunner.destructiveConfirm);
      if (!confirmed) return;
    }

    let jsonBody: unknown = null;
    if (shouldShowBody(selectedEndpoint.method) && bodyText.trim()) {
      try {
        jsonBody = JSON.parse(bodyText);
      } catch {
        setError(t.testRunner.invalidJson);
        return;
      }
    }

    const validationErrors = validateRequiredInputs(
      selectedEndpoint,
      rowsToRecord(pathRows),
      rowsToRecord(queryRows),
      jsonBody
    );
    if (validationErrors.length > 0) {
      setError(`${t.testRunner.missingRequiredFields}: ${validationErrors.join(", ")}`);
      return;
    }

    const payload: TestRequestPayload = {
      path_params: rowsToRecord(pathRows),
      query_params: rowsToRecord(queryRows),
      headers: rowsToStringRecord(headerRows),
      bearer_token: bearerToken.trim() || null,
      json_body: shouldShowBody(selectedEndpoint.method) ? jsonBody : null
    };

    setLoading(true);
    try {
      const result = await runEndpointTest(selectedProjectId, selectedEndpoint.id, payload);
      setLatestRun(result);
      const [endpointData, runData] = await Promise.all([
        listEndpoints(selectedProjectId),
        listTestRuns(selectedProjectId)
      ]);
      setEndpoints(endpointData);
      setTestRuns(runData);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.testRunner.runFailed);
    } finally {
      setLoading(false);
    }
  }

  if (!selectedProjectId || !selectedProject) {
    return (
      <section className="page-stack">
        <PageHeader subtitle={t.placeholders.testRunnerSubtitle} title={t.placeholders.testRunnerTitle} />
        <Card>
          <div className="empty-panel">
            <h2>{t.testRunner.noProjectTitle}</h2>
            <p>{t.testRunner.noProjectDescription}</p>
            <button className="primary-button" onClick={() => onNavigate("setup")} type="button">
              {t.nav.projectSetup}
            </button>
          </div>
        </Card>
      </section>
    );
  }

  return (
    <section className="page-stack">
      <PageHeader
        actions={
          <button className="outline-button" disabled={loading} onClick={() => void refreshData()} type="button">
            {t.common.refresh}
          </button>
        }
        subtitle={t.placeholders.testRunnerSubtitle}
        title={t.placeholders.testRunnerTitle}
      />

      {error ? <div className="notice danger">{error}</div> : null}

      <div className="stat-grid four">
        <StatCard icon={ShieldCheck} title={t.testRunner.passedRuns} value={passedCount} hint={selectedProject.name} tone="green" />
        <StatCard icon={XCircle} title={t.testRunner.failedRuns} value={failedCount} hint={t.testRunner.recentRuns} tone="red" />
        <StatCard icon={Clock3} title={t.testRunner.avgResponseTime} value={avgResponseTime} hint={t.testRunner.recentRuns} tone="blue" />
        <StatCard icon={Code2} title={t.testRunner.availableEndpoints} value={endpoints.length} hint={selectedProject.name} tone="purple" />
      </div>

      <div className="split-grid test">
        <Card>
          <div className="card-heading">
            <h2>{t.testRunner.requestSetup}</h2>
            <StatusBadge tone={loading ? "warning" : "info"}>
              {loading ? t.common.checking : selectedProject.name}
            </StatusBadge>
          </div>

          {endpoints.length === 0 ? (
            <div className="empty-panel compact">
              <h2>{t.testRunner.noEndpointsTitle}</h2>
              <p>{t.testRunner.noEndpointsDescription}</p>
              <button className="primary-button" onClick={() => onNavigate("apiMap")} type="button">
                {t.nav.apiMap}
              </button>
            </div>
          ) : (
            <div className="runner-form">
              <label className="form-field">
                {t.testRunner.endpoint}
                <select
                  value={selectedEndpointId ?? ""}
                  onChange={(event) => setSelectedEndpointId(Number(event.target.value))}
                >
                  {endpoints.map((endpoint) => (
                    <option key={endpoint.id} value={endpoint.id}>
                      {endpoint.method} {endpoint.path}
                    </option>
                  ))}
                </select>
              </label>

              <div className="runner-url-row">
                <StatusBadge tone={methodTone(selectedEndpoint?.method ?? "")}>{selectedEndpoint?.method ?? "-"}</StatusBadge>
                <code>{computedUrl}</code>
              </div>

              {selectedEndpoint && destructiveMethods.has(selectedEndpoint.method.toUpperCase()) ? (
                <div className="notice danger runner-warning">
                  <AlertTriangle size={16} />
                  {t.testRunner.destructiveWarning}
                </div>
              ) : null}

              <KeyValueEditor
                rows={pathRows}
                setRows={setPathRows}
                title={t.testRunner.pathParams}
                valuePlaceholder={t.testRunner.value}
              />
              <KeyValueEditor
                rows={queryRows}
                setRows={setQueryRows}
                title={t.testRunner.queryParams}
                valuePlaceholder={t.testRunner.value}
              />
              <KeyValueEditor
                rows={headerRows}
                setRows={setHeaderRows}
                title={t.testRunner.headers}
                valuePlaceholder={t.testRunner.value}
              />

              <label className="form-field">
                {t.testRunner.bearerToken}
                <input
                  onChange={(event) => setBearerToken(event.target.value)}
                  placeholder="eyJhbGci..."
                  type="password"
                  value={bearerToken}
                />
              </label>

              {selectedEndpoint && shouldShowBody(selectedEndpoint.method) ? (
                <label className="form-field">
                  {t.testRunner.jsonBody}
                  <textarea
                    className="json-editor"
                    onChange={(event) => setBodyText(event.target.value)}
                    spellCheck={false}
                    value={bodyText}
                  />
                </label>
              ) : null}

              <button
                className="primary-button full-width"
                disabled={loading || !selectedEndpoint}
                onClick={() => void runTest()}
                type="button"
              >
                <Play size={17} />
                {loading ? t.common.checking : t.testRunner.runTest}
              </button>
            </div>
          )}
        </Card>

        <ResultPanel latestRun={latestRun} t={t} />
      </div>

      <Card>
        <div className="card-heading">
          <h2>{t.testRunner.recentRuns}</h2>
          <StatusBadge tone="neutral">{testRuns.length}</StatusBadge>
        </div>
        {testRuns.length === 0 ? (
          <div className="empty-panel compact">{t.testRunner.noRuns}</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>{t.apiMap.method}</th>
                <th>URL</th>
                <th>{t.apiMap.testStatus}</th>
                <th>{t.apiMap.lastStatus}</th>
                <th>{t.apiMap.latency}</th>
                <th>{t.testRunner.dbChangeSummary}</th>
                <th>{t.testRunner.createdAt}</th>
              </tr>
            </thead>
            <tbody>
              {testRuns.map((run) => (
                <tr key={run.id} onClick={() => setLatestRun(run)}>
                  <td><StatusBadge tone={methodTone(run.method)}>{run.method}</StatusBadge></td>
                  <td>{run.url}</td>
                  <td><StatusBadge tone={statusTone(run.status)}>{run.status}</StatusBadge></td>
                  <td>{run.http_status ?? "-"}</td>
                  <td>{run.response_time_ms != null ? `${run.response_time_ms} ms` : "-"}</td>
                  <td><DbChangesSummary dbChanges={run.db_changes} t={t} /></td>
                  <td>{new Date(run.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </section>
  );
}

function ResultPanel({ latestRun, t }: { latestRun: TestRun | null; t: Messages }) {
  if (!latestRun) {
    return (
      <Card>
        <div className="empty-panel">
          <h2>{t.testRunner.latestResult}</h2>
          <p>{t.testRunner.noResult}</p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="card-heading">
        <h2>{t.testRunner.latestResult}</h2>
        <StatusBadge tone={statusTone(latestRun.status)}>{latestRun.status}</StatusBadge>
      </div>
      <div className={`result-number ${latestRun.status === "failed" ? "failed" : ""}`}>
        {latestRun.http_status ?? "-"}
        <span>{latestRun.response_time_ms != null ? `${latestRun.response_time_ms} ms` : t.common.error}</span>
      </div>
      {latestRun.error_message ? <div className="notice danger">{latestRun.error_message}</div> : null}
      <ValidationFailurePanel responseBody={latestRun.response_body} statusCode={latestRun.http_status} t={t} />
      <DbChangesPanel dbChanges={latestRun.db_changes} t={t} />
      <SchemaBlock title={t.testRunner.responseBody} value={latestRun.response_body} />
      <SchemaBlock title={t.testRunner.responseHeaders} value={latestRun.response_headers} />
      <SchemaBlock title={t.testRunner.requestRecord} value={{
        headers: latestRun.request_headers,
        query: latestRun.request_query_params,
        path: latestRun.request_path_params,
        body: latestRun.request_body
      }} />
    </Card>
  );
}

function DbChangesPanel({ dbChanges, t }: { dbChanges?: DbChanges; t: Messages }) {
  if (!dbChanges) return null;

  if (dbChanges.status === "skipped") {
    return (
      <div className="db-change-panel skipped">
        <div className="card-heading">
          <h2>{t.testRunner.databaseChanges}</h2>
          <StatusBadge tone="warning">{t.testRunner.skipped}</StatusBadge>
        </div>
        <p>{dbChanges.warning_message || t.testRunner.databaseChangesSkipped}</p>
      </div>
    );
  }

  if (dbChanges.status === "error") {
    return (
      <div className="db-change-panel error">
        <div className="card-heading">
          <h2>{t.testRunner.databaseChanges}</h2>
          <StatusBadge tone="danger">{t.common.error}</StatusBadge>
        </div>
        <p>{dbChanges.warning_message || t.testRunner.databaseChangesError}</p>
      </div>
    );
  }

  if (!dbChanges.changed) {
    return (
      <div className="db-change-panel">
        <div className="card-heading">
          <h2>{t.testRunner.databaseChanges}</h2>
          <StatusBadge tone="neutral">{t.testRunner.noChanges}</StatusBadge>
        </div>
        <p>{t.testRunner.noDatabaseChanges}</p>
      </div>
    );
  }

  return (
    <div className="db-change-panel changed">
      <div className="card-heading">
        <h2>{t.testRunner.databaseChanges}</h2>
        <StatusBadge tone="success">
          {dbChanges.tables_modified.length} {t.testRunner.changedTables}
        </StatusBadge>
      </div>

      <div className="db-change-grid">
        <ChangeList title={t.testRunner.tablesAdded} values={dbChanges.tables_added} />
        <ChangeList title={t.testRunner.tablesRemoved} values={dbChanges.tables_removed} />
      </div>

      {Object.keys(dbChanges.row_count_diff).length > 0 ? (
        <section className="detail-section">
          <h3 className="schema-title">{t.testRunner.rowCountChanges}</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Table</th>
                <th>Before</th>
                <th>After</th>
                <th>Diff</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(dbChanges.row_count_diff).map(([table, diff]) => (
                <tr key={table}>
                  <td>{table}</td>
                  <td>{diff.before}</td>
                  <td>{diff.after}</td>
                  <td>{diff.diff > 0 ? `+${diff.diff}` : diff.diff}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      {Object.keys(dbChanges.schema_diff).length > 0 ? (
        <SchemaBlock title={t.testRunner.schemaChanges} value={dbChanges.schema_diff} />
      ) : null}

      {Object.keys(dbChanges.sample_diff).length > 0 ? (
        <SchemaBlock title={t.testRunner.sampleChanges} value={dbChanges.sample_diff} />
      ) : null}
    </div>
  );
}

function DbChangesSummary({ dbChanges, t }: { dbChanges?: DbChanges; t: Messages }) {
  if (!dbChanges) return <StatusBadge tone="neutral">-</StatusBadge>;
  if (dbChanges.status === "error") return <StatusBadge tone="danger">{t.common.error}</StatusBadge>;
  if (dbChanges.status === "skipped") return <StatusBadge tone="warning">{t.testRunner.skipped}</StatusBadge>;
  if (!dbChanges.changed) return <StatusBadge tone="neutral">{t.testRunner.noChanges}</StatusBadge>;
  return <StatusBadge tone="success">{dbChanges.tables_modified.length}</StatusBadge>;
}

function ChangeList({ title, values }: { title: string; values: string[] }) {
  return (
    <section className="db-change-list">
      <strong>{title}</strong>
      {values.length ? (
        <div>
          {values.map((value) => (
            <span key={value}>{value}</span>
          ))}
        </div>
      ) : (
        <p>-</p>
      )}
    </section>
  );
}

function ValidationFailurePanel({
  responseBody,
  statusCode,
  t
}: {
  responseBody: unknown;
  statusCode?: number | null;
  t: Messages;
}) {
  const details = extractValidationDetails(responseBody);
  if (statusCode !== 422) return null;

  return (
    <div className="validation-panel">
      <strong>{t.testRunner.validationFailed}</strong>
      {details.length > 0 ? (
        <ul>
          {details.map((detail, index) => (
            <li key={`${detail.location}-${index}`}>
              <code>{detail.location}</code>
              <span>{detail.message}</span>
              <em>{detail.type}</em>
            </li>
          ))}
        </ul>
      ) : (
        <p>{t.testRunner.validationFailedDescription}</p>
      )}
    </div>
  );
}

function KeyValueEditor({
  rows,
  setRows,
  title,
  valuePlaceholder
}: {
  rows: KeyValueRow[];
  setRows: (rows: KeyValueRow[]) => void;
  title: string;
  valuePlaceholder: string;
}) {
  return (
    <section className="key-value-editor">
      <div className="section-heading">
        <h2>{title}</h2>
        <button className="ghost-button compact" onClick={() => setRows([...rows, { id: createId(), key: "", value: "" }])} type="button">
          +
        </button>
      </div>
      <div className="key-value-rows">
        {rows.map((row) => (
          <div className="key-value-row" key={row.id}>
            <input
              onChange={(event) => updateRow(rows, setRows, row.id, "key", event.target.value)}
              placeholder="key"
              value={row.key}
            />
            <input
              onChange={(event) => updateRow(rows, setRows, row.id, "value", event.target.value)}
              placeholder={valuePlaceholder}
              value={row.value}
            />
            <button
              className="icon-only"
              onClick={() => setRows(rows.filter((item) => item.id !== row.id))}
              type="button"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}

function SchemaBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <section className="detail-section">
      <h3 className="schema-title">{title}</h3>
      <div className="code-block">{formatValue(value)}</div>
    </section>
  );
}

function rowsFromParameters(parameters: Record<string, unknown>[]): KeyValueRow[] {
  const rows = parameters
    .map((parameter) => ({
      id: createId(),
      key: typeof parameter.name === "string" ? parameter.name : "",
      value: stringifyFormValue(sampleValue(readSchema(parameter.schema)))
    }))
    .filter((row) => row.key);
  return rows.length ? rows : [{ id: createId(), key: "", value: "" }];
}

function rowsToRecord(rows: KeyValueRow[]): Record<string, unknown> {
  return rows.reduce<Record<string, unknown>>((record, row) => {
    if (row.key.trim()) record[row.key.trim()] = coerceValue(row.value);
    return record;
  }, {});
}

function rowsToStringRecord(rows: KeyValueRow[]): Record<string, string> {
  return rows.reduce<Record<string, string>>((record, row) => {
    if (row.key.trim()) record[row.key.trim()] = row.value;
    return record;
  }, {});
}

function updateRow(
  rows: KeyValueRow[],
  setRows: (rows: KeyValueRow[]) => void,
  id: string,
  field: "key" | "value",
  value: string
) {
  setRows(rows.map((row) => (row.id === id ? { ...row, [field]: value } : row)));
}

function createBodyExample(schema: Record<string, unknown>): unknown {
  return sampleValue(schema);
}

function sampleValue(schema: Record<string, unknown>): unknown {
  if ("example" in schema) return schema.example;
  if ("default" in schema) return schema.default;
  if (schema.format === "uuid") return "00000000-0000-0000-0000-000000000000";
  if (schema.format === "date-time") return new Date().toISOString();
  if (schema.format === "date") return "2026-05-09";
  if (schema.type === "integer" || schema.type === "number") return 1;
  if (schema.type === "boolean") return true;
  if (schema.type === "array") return [];
  if (schema.type === "object" || isObjectSchema(schema)) return sampleObject(schema);
  return "string";
}

function sampleObject(schema: Record<string, unknown>): Record<string, unknown> {
  const properties = schema.properties;
  if (!isRecord(properties)) return {};
  return Object.entries(properties).reduce<Record<string, unknown>>((example, [key, value]) => {
    example[key] = sampleValue(readSchema(value));
    return example;
  }, {});
}

function validateRequiredInputs(
  endpoint: Endpoint,
  pathParams: Record<string, unknown>,
  queryParams: Record<string, unknown>,
  jsonBody: unknown
): string[] {
  const missing: string[] = [];
  for (const parameter of endpoint.path_params) {
    const name = typeof parameter.name === "string" ? parameter.name : "";
    if (name && (parameter.required === true || endpoint.path.includes(`{${name}}`)) && isEmptyValue(pathParams[name])) {
      missing.push(`path.${name}`);
    }
  }
  for (const parameter of endpoint.query_params) {
    const name = typeof parameter.name === "string" ? parameter.name : "";
    if (name && parameter.required === true && isEmptyValue(queryParams[name])) {
      missing.push(`query.${name}`);
    }
  }
  if (shouldShowBody(endpoint.method)) {
    missing.push(...missingRequiredBodyFields(endpoint.request_body_schema, jsonBody, "body"));
  }
  return missing;
}

function missingRequiredBodyFields(schema: Record<string, unknown>, value: unknown, prefix: string): string[] {
  const required = Array.isArray(schema.required) ? schema.required.filter((item): item is string => typeof item === "string") : [];
  if (!required.length) return [];
  if (!isRecord(value)) return required.map((field) => `${prefix}.${field}`);
  const properties = isRecord(schema.properties) ? schema.properties : {};
  return required.flatMap((field) => {
    const fieldPath = `${prefix}.${field}`;
    if (isEmptyValue(value[field])) return [fieldPath];
    const childSchema = readSchema(properties[field]);
    if (isObjectSchema(childSchema)) {
      return missingRequiredBodyFields(childSchema, value[field], fieldPath);
    }
    return [];
  });
}

function extractValidationDetails(responseBody: unknown): Array<{ location: string; message: string; type: string }> {
  if (!isRecord(responseBody) || !Array.isArray(responseBody.detail)) return [];
  return responseBody.detail
    .map((detail) => {
      if (!isRecord(detail)) return null;
      const loc = Array.isArray(detail.loc) ? detail.loc.map(String).join(".") : "request";
      return {
        location: loc,
        message: typeof detail.msg === "string" ? detail.msg : "Validation error",
        type: typeof detail.type === "string" ? detail.type : "-"
      };
    })
    .filter((detail): detail is { location: string; message: string; type: string } => detail !== null);
}

function readSchema(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function isObjectSchema(schema: Record<string, unknown>): boolean {
  return schema.type === "object" || isRecord(schema.properties);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isEmptyValue(value: unknown): boolean {
  return value === undefined || value === null || value === "";
}

function stringifyFormValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function coerceValue(value: string): unknown {
  if (value === "true") return true;
  if (value === "false") return false;
  if (value.trim() !== "" && !Number.isNaN(Number(value))) return Number(value);
  return value;
}

function shouldShowBody(method: string): boolean {
  return ["POST", "PUT", "PATCH", "DELETE"].includes(method.toUpperCase());
}

function joinUrl(baseUrl: string, path: string): string {
  return `${baseUrl.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;
}

function createId(): string {
  return Math.random().toString(36).slice(2);
}

function formatValue(value: unknown): string {
  if (typeof value === "string") return value;
  return JSON.stringify(value ?? null, null, 2);
}

function methodTone(method: string): StatusTone {
  if (method === "GET") return "info";
  if (method === "POST") return "success";
  if (method === "PUT" || method === "PATCH") return "warning";
  if (method === "DELETE") return "danger";
  return "neutral";
}

function statusTone(status: string): StatusTone {
  if (status === "passed") return "success";
  if (status === "failed") return "danger";
  if (status === "skipped") return "warning";
  return "neutral";
}
