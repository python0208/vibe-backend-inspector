import { FileUp, Network, Pencil, Play, Plus, RefreshCw, Search, ShieldCheck, Trash2, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  autoDetectOpenApi,
  createEndpoint,
  deleteEndpoint,
  discoverOpenApi,
  importOpenApiFile,
  listEndpoints,
  updateEndpoint
} from "../api/endpoints";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/ui/StatCard";
import { StatusBadge, type StatusTone } from "../components/ui/StatusBadge";
import type { Messages } from "../i18n";
import type { Endpoint, EndpointMutationPayload, HttpMethod } from "../types/api";
import type { PageKey } from "../types/navigation";
import type { ProjectListItem } from "../types/project";

interface ApiMapProps {
  t: Messages;
  projects: ProjectListItem[];
  selectedProjectId: number | null;
  onNavigate: (page: PageKey) => void;
  onProjectsChanged: () => Promise<void>;
  onEndpointTestSelected: (endpointId: number) => void;
}

const methods: Array<HttpMethod | "ALL"> = ["ALL", "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"];
const statuses = ["ALL", "untested", "passed", "failed", "skipped"];
const sources = ["ALL", "openapi_url", "openapi_file", "manual"];

interface EndpointFormState {
  method: HttpMethod;
  path: string;
  summary: string;
  description: string;
  tags: string;
  auth_required: boolean;
  requestBodySchema: string;
  responseSchema: string;
}

const emptyEndpointForm: EndpointFormState = {
  method: "GET",
  path: "/api/example",
  summary: "",
  description: "",
  tags: "",
  auth_required: false,
  requestBodySchema: "{}",
  responseSchema: "{}"
};

export function ApiMap({
  t,
  projects,
  selectedProjectId,
  onNavigate,
  onProjectsChanged,
  onEndpointTestSelected
}: ApiMapProps) {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [selectedEndpointId, setSelectedEndpointId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [methodFilter, setMethodFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [sourceFilter, setSourceFilter] = useState<string>("ALL");
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [savingEndpoint, setSavingEndpoint] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingEndpoint, setEditingEndpoint] = useState<Endpoint | null>(null);
  const [endpointForm, setEndpointForm] = useState<EndpointFormState>(emptyEndpointForm);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedProject = projects.find((project) => project.id === selectedProjectId) ?? null;

  async function refreshEndpoints(projectId = selectedProjectId) {
    if (!projectId) {
      setEndpoints([]);
      setSelectedEndpointId(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await listEndpoints(projectId);
      setEndpoints(data);
      setSelectedEndpointId((current) => current ?? data[0]?.id ?? null);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Unable to load endpoints.");
      setEndpoints([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshEndpoints();
  }, [selectedProjectId]);

  async function syncOpenApi() {
    if (!selectedProjectId || !selectedProject) {
      return;
    }
    setLoading(true);
    setMessage(null);
    setError(null);
    try {
      const result = selectedProject.openapi_url
        ? await discoverOpenApi(selectedProjectId)
        : await autoDetectOpenApi(selectedProjectId);
      if (!result.ok) {
        setError(result.message);
        return;
      }
      setMessage(`${t.apiMap.discoveryCompleted} ${result.created} created, ${result.updated} updated.`);
      await onProjectsChanged();
      await refreshEndpoints(selectedProjectId);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "OpenAPI discovery failed.");
    } finally {
      setLoading(false);
    }
  }

  async function importSelectedFile() {
    if (!selectedProjectId || !selectedFile) {
      return;
    }
    setImporting(true);
    setMessage(null);
    setError(null);
    try {
      const result = await importOpenApiFile(selectedProjectId, selectedFile);
      setMessage(`${t.apiMap.importCompleted} ${result.created} created, ${result.updated} updated.`);
      setSelectedFile(null);
      await refreshEndpoints(selectedProjectId);
    } catch (exc) {
      setError(readErrorMessage(exc, "OpenAPI file import failed."));
    } finally {
      setImporting(false);
    }
  }

  function openCreateForm() {
    setEditingEndpoint(null);
    setEndpointForm(emptyEndpointForm);
    setFormOpen(true);
    setError(null);
  }

  function openEditForm(endpoint: Endpoint) {
    setEditingEndpoint(endpoint);
    setEndpointForm({
      method: normalizeMethod(endpoint.method),
      path: endpoint.path,
      summary: endpoint.summary ?? "",
      description: endpoint.description ?? "",
      tags: endpoint.tags.join(", "),
      auth_required: endpoint.auth_required,
      requestBodySchema: JSON.stringify(endpoint.request_body_schema, null, 2),
      responseSchema: JSON.stringify(endpoint.response_schema, null, 2)
    });
    setFormOpen(true);
    setError(null);
  }

  async function saveManualEndpoint() {
    if (!selectedProjectId) return;
    setSavingEndpoint(true);
    setError(null);
    try {
      const payload = endpointFormToPayload(endpointForm, t);
      const saved = editingEndpoint
        ? await updateEndpoint(selectedProjectId, editingEndpoint.id, payload)
        : await createEndpoint(selectedProjectId, payload);
      setMessage(t.apiMap.manualEndpointSaved);
      setSelectedEndpointId(saved.id);
      setFormOpen(false);
      setEditingEndpoint(null);
      await refreshEndpoints(selectedProjectId);
    } catch (exc) {
      setError(readErrorMessage(exc, "Unable to save endpoint."));
    } finally {
      setSavingEndpoint(false);
    }
  }

  async function removeManualEndpoint(endpoint: Endpoint) {
    if (!selectedProjectId || !window.confirm(t.apiMap.confirmDeleteEndpoint)) {
      return;
    }
    setLoading(true);
    setMessage(null);
    setError(null);
    try {
      await deleteEndpoint(selectedProjectId, endpoint.id);
      setMessage(t.apiMap.endpointDeleted);
      setSelectedEndpointId(null);
      await refreshEndpoints(selectedProjectId);
    } catch (exc) {
      setError(readErrorMessage(exc, "Unable to delete endpoint."));
    } finally {
      setLoading(false);
    }
  }

  const filteredEndpoints = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return endpoints.filter((endpoint) => {
      const matchesSearch =
        !normalizedSearch ||
        endpoint.path.toLowerCase().includes(normalizedSearch) ||
        (endpoint.summary ?? "").toLowerCase().includes(normalizedSearch);
      const matchesMethod = methodFilter === "ALL" || endpoint.method === methodFilter;
      const matchesStatus = statusFilter === "ALL" || endpoint.test_status === statusFilter;
      const matchesSource = sourceFilter === "ALL" || sourceGroup(endpoint.source) === sourceFilter;
      return matchesSearch && matchesMethod && matchesStatus && matchesSource;
    });
  }, [endpoints, methodFilter, search, sourceFilter, statusFilter]);

  const selectedEndpoint =
    filteredEndpoints.find((endpoint) => endpoint.id === selectedEndpointId) ??
    filteredEndpoints[0] ??
    null;
  const testedCount = endpoints.filter((endpoint) => endpoint.test_status !== "untested").length;
  const failedCount = endpoints.filter((endpoint) => endpoint.test_status === "failed").length;

  if (!selectedProjectId || !selectedProject) {
    return (
      <section className="page-stack">
        <PageHeader subtitle={t.placeholders.apiMapSubtitle} title={t.placeholders.apiMapTitle} />
        <Card>
          <div className="empty-panel">
            <h2>{t.apiMap.noProjectTitle}</h2>
            <p>{t.apiMap.noProjectDescription}</p>
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
          <div className="api-action-row">
            <button className="primary-button" disabled={loading} onClick={() => void syncOpenApi()} type="button">
              <RefreshCw size={17} />
              {selectedProject.openapi_url ? t.apiMap.syncOpenApi : t.apiMap.autoDetectOpenApi}
            </button>
            <button className="outline-button" disabled={loading} onClick={openCreateForm} type="button">
              <Plus size={17} />
              {t.apiMap.addManualEndpoint}
            </button>
          </div>
        }
        subtitle={t.placeholders.apiMapSubtitle}
        title={t.placeholders.apiMapTitle}
      />

      <Card className="api-source-card">
        <div className="card-heading">
          <div>
            <h2>{t.apiMap.importOpenApiFile}</h2>
            <p>{t.apiMap.selectOpenApiFile}</p>
          </div>
          <StatusBadge tone="info">{t.apiMap.sourceOpenApiFile}</StatusBadge>
        </div>
        <div className="file-import-row">
          <input
            accept=".json,.yaml,.yml,application/json,application/yaml,text/yaml"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            type="file"
          />
          <button
            className="outline-button"
            disabled={importing || !selectedFile}
            onClick={() => void importSelectedFile()}
            type="button"
          >
            <FileUp size={17} />
            {importing ? t.common.checking : t.apiMap.importOpenApiFile}
          </button>
        </div>
      </Card>

      <div className="filter-bar api-filters">
        <label className="filter-field">
          <span>{t.apiMap.method}</span>
          <select value={methodFilter} onChange={(event) => setMethodFilter(event.target.value)}>
            {methods.map((method) => (
              <option key={method} value={method}>
                {method === "ALL" ? t.apiMap.allMethods : method}
              </option>
            ))}
          </select>
        </label>
        <label className="filter-field">
          <span>{t.apiMap.testStatus}</span>
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            {statuses.map((status) => (
              <option key={status} value={status}>
                {status === "ALL" ? t.apiMap.allStatus : status}
              </option>
            ))}
          </select>
        </label>
        <label className="filter-field">
          <span>{t.apiMap.source}</span>
          <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}>
            {sources.map((source) => (
              <option key={source} value={source}>
                {source === "ALL" ? t.apiMap.allSources : sourceLabel(source, t)}
              </option>
            ))}
          </select>
        </label>
        <label className="table-search">
          <Search size={17} />
          <input
            onChange={(event) => setSearch(event.target.value)}
            placeholder={t.common.searchPlaceholder}
            value={search}
          />
        </label>
      </div>

      {message ? <div className="notice success">{message}</div> : null}
      {error ? <div className="notice danger">{error}</div> : null}

      <div className="stat-grid three">
        <StatCard icon={Network} title={t.apiMap.totalEndpoints} value={endpoints.length} hint={selectedProject.name} tone="blue" />
        <StatCard icon={ShieldCheck} title={t.apiMap.testedEndpoints} value={testedCount} hint={t.common.phaseNotice} tone="purple" />
        <StatCard icon={XCircle} title={t.apiMap.failedEndpoints} value={failedCount} hint={t.common.phaseNotice} tone="red" />
      </div>

      <div className="split-grid api">
        <Card>
          <div className="card-heading">
            <h2>{filteredEndpoints.length} endpoints</h2>
            <StatusBadge tone={loading ? "warning" : "info"}>
              {loading ? t.common.checking : selectedProject.name}
            </StatusBadge>
          </div>

          {filteredEndpoints.length === 0 ? (
            <div className="empty-panel">
              <h2>{t.apiMap.noEndpointsTitle}</h2>
              <p>{t.apiMap.noEndpointsDescription}</p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t.apiMap.method}</th>
                  <th>{t.apiMap.path}</th>
                  <th>{t.apiMap.summary}</th>
                  <th>{t.apiMap.source}</th>
                  <th>{t.apiMap.auth}</th>
                  <th>{t.apiMap.testStatus}</th>
                  <th>{t.apiMap.lastStatus}</th>
                  <th>{t.apiMap.latency}</th>
                  <th>{t.apiMap.actions}</th>
                </tr>
              </thead>
              <tbody>
                {filteredEndpoints.map((endpoint) => (
                  <tr
                    className={endpoint.id === selectedEndpoint?.id ? "selected-row" : ""}
                    key={endpoint.id}
                    onClick={() => setSelectedEndpointId(endpoint.id)}
                  >
                    <td><StatusBadge tone={methodTone(endpoint.method)}>{endpoint.method}</StatusBadge></td>
                    <td>{endpoint.path}</td>
                    <td>{endpoint.summary || "-"}</td>
                    <td><StatusBadge tone={sourceTone(endpoint.source)}>{sourceLabel(endpoint.source, t)}</StatusBadge></td>
                    <td>{endpoint.auth_required ? "Bearer" : "None"}</td>
                    <td><StatusBadge tone={statusTone(endpoint.test_status)}>{endpoint.test_status}</StatusBadge></td>
                    <td>{endpoint.last_status_code ?? "-"}</td>
                    <td>{endpoint.last_response_time_ms ? `${endpoint.last_response_time_ms} ms` : "-"}</td>
                    <td>
                      <button
                        className="icon-only"
                        onClick={(event) => {
                          event.stopPropagation();
                          setSelectedEndpointId(endpoint.id);
                          onEndpointTestSelected(endpoint.id);
                          onNavigate("testRunner");
                        }}
                        type="button"
                      >
                        <Play size={14} />
                      </button>
                      {sourceGroup(endpoint.source) === "manual" ? (
                        <>
                          <button
                            className="icon-only"
                            onClick={(event) => {
                              event.stopPropagation();
                              openEditForm(endpoint);
                            }}
                            title={t.apiMap.editEndpoint}
                            type="button"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            className="icon-only danger"
                            onClick={(event) => {
                              event.stopPropagation();
                              void removeManualEndpoint(endpoint);
                            }}
                            title={t.apiMap.deleteEndpoint}
                            type="button"
                          >
                            <Trash2 size={14} />
                          </button>
                        </>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <EndpointDetail endpoint={selectedEndpoint} t={t} />
      </div>

      {formOpen ? (
        <ManualEndpointModal
          form={endpointForm}
          isEditing={Boolean(editingEndpoint)}
          loading={savingEndpoint}
          onCancel={() => {
            setFormOpen(false);
            setEditingEndpoint(null);
          }}
          onChange={setEndpointForm}
          onSave={() => void saveManualEndpoint()}
          t={t}
        />
      ) : null}
    </section>
  );
}

function EndpointDetail({ endpoint, t }: { endpoint: Endpoint | null; t: Messages }) {
  if (!endpoint) {
    return (
      <Card>
        <div className="endpoint-panel">
          <h2>{t.apiMap.endpointInfo}</h2>
          <p>{t.apiMap.selectEndpoint}</p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="endpoint-panel">
        <div className="endpoint-title">
          <StatusBadge tone={methodTone(endpoint.method)}>{endpoint.method}</StatusBadge>
          <h2>{endpoint.path}</h2>
        </div>
        <div className="summary-table">
          <DetailRow label={t.apiMap.operationId} value={endpoint.operation_id || "-"} />
          <DetailRow label={t.apiMap.tags} value={endpoint.tags.length ? endpoint.tags.join(", ") : "-"} />
          <DetailRow label={t.apiMap.authRequired} value={endpoint.auth_required ? "true" : "false"} />
          <DetailRow label={t.apiMap.source} value={sourceLabel(endpoint.source, t)} />
        </div>
        <SchemaBlock title={t.apiMap.queryParams} value={endpoint.query_params} />
        <SchemaBlock title={t.apiMap.pathParams} value={endpoint.path_params} />
        <SchemaBlock title={t.apiMap.requestSchema} value={endpoint.request_body_schema} />
        <SchemaBlock title={t.apiMap.responseSchema} value={endpoint.response_schema} />
      </div>
    </Card>
  );
}

function ManualEndpointModal({
  form,
  isEditing,
  loading,
  onCancel,
  onChange,
  onSave,
  t
}: {
  form: EndpointFormState;
  isEditing: boolean;
  loading: boolean;
  onCancel: () => void;
  onChange: (form: EndpointFormState) => void;
  onSave: () => void;
  t: Messages;
}) {
  const updateField = <K extends keyof EndpointFormState>(key: K, value: EndpointFormState[K]) => {
    onChange({ ...form, [key]: value });
  };

  return (
    <div className="modal-backdrop" role="presentation">
      <div aria-modal="true" className="modal-panel endpoint-modal" role="dialog">
        <div className="card-heading">
          <div>
            <h2>{isEditing ? t.apiMap.editEndpoint : t.apiMap.endpointFormTitle}</h2>
            <p>{t.apiMap.endpointFormSubtitle}</p>
          </div>
          <StatusBadge tone="warning">{t.apiMap.sourceManual}</StatusBadge>
        </div>

        <div className="form-grid two">
          <label className="form-field">
            {t.apiMap.method}
            <select value={form.method} onChange={(event) => updateField("method", event.target.value as HttpMethod)}>
              {methods.filter((method) => method !== "ALL").map((method) => (
                <option key={method} value={method}>
                  {method}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            {t.apiMap.path}
            <input value={form.path} onChange={(event) => updateField("path", event.target.value)} />
          </label>
          <label className="form-field">
            {t.apiMap.summary}
            <input value={form.summary} onChange={(event) => updateField("summary", event.target.value)} />
          </label>
          <label className="form-field">
            {t.apiMap.tags}
            <input value={form.tags} onChange={(event) => updateField("tags", event.target.value)} />
          </label>
        </div>

        <label className="form-field">
          {t.apiMap.description}
          <textarea value={form.description} onChange={(event) => updateField("description", event.target.value)} />
        </label>

        <label className="checkbox-row">
          <input
            checked={form.auth_required}
            onChange={(event) => updateField("auth_required", event.target.checked)}
            type="checkbox"
          />
          <span>{t.apiMap.authRequired}</span>
        </label>

        <div className="form-grid two">
          <label className="form-field">
            {t.apiMap.requestSchema}
            <textarea
              className="schema-textarea"
              value={form.requestBodySchema}
              onChange={(event) => updateField("requestBodySchema", event.target.value)}
            />
          </label>
          <label className="form-field">
            {t.apiMap.responseSchema}
            <textarea
              className="schema-textarea"
              value={form.responseSchema}
              onChange={(event) => updateField("responseSchema", event.target.value)}
            />
          </label>
        </div>

        <div className="modal-actions">
          <button className="ghost-button" onClick={onCancel} type="button">
            {t.common.cancel}
          </button>
          <button className="primary-button" disabled={loading} onClick={onSave} type="button">
            {loading ? t.common.checking : t.common.save}
          </button>
        </div>
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="summary-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SchemaBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <section>
      <h3 className="schema-title">{title}</h3>
      <div className="code-block">{JSON.stringify(value, null, 2)}</div>
    </section>
  );
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

function sourceGroup(source: string): string {
  if (source === "openapi_file") return "openapi_file";
  if (source === "manual") return "manual";
  return "openapi_url";
}

function sourceTone(source: string): StatusTone {
  if (sourceGroup(source) === "openapi_file") return "warning";
  if (sourceGroup(source) === "manual") return "success";
  return "info";
}

function sourceLabel(source: string, t: Messages): string {
  const group = sourceGroup(source);
  if (group === "openapi_file") return t.apiMap.sourceOpenApiFile;
  if (group === "manual") return t.apiMap.sourceManual;
  return t.apiMap.sourceOpenApiUrl;
}

function normalizeMethod(method: string): HttpMethod {
  const upper = method.toUpperCase();
  return methods.includes(upper as HttpMethod) && upper !== "ALL" ? (upper as HttpMethod) : "GET";
}

function endpointFormToPayload(form: EndpointFormState, t: Messages): EndpointMutationPayload {
  const path = form.path.trim();
  if (!path.startsWith("/")) {
    throw new Error("Endpoint path must start with '/'.");
  }

  return {
    method: form.method,
    path,
    summary: form.summary.trim() || null,
    description: form.description.trim() || null,
    operation_id: null,
    tags: form.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
    query_params: [],
    path_params: extractPathParams(path),
    request_body_schema: parseJsonObject(form.requestBodySchema, t),
    response_schema: parseJsonObject(form.responseSchema, t),
    auth_required: form.auth_required
  };
}

function extractPathParams(path: string): Record<string, unknown>[] {
  const matches = path.matchAll(/\{([^{}]+)\}/g);
  return Array.from(matches).map((match) => ({
    name: match[1],
    in: "path",
    required: true,
    schema: { type: "string" }
  }));
}

function parseJsonObject(value: string, t: Messages): Record<string, unknown> {
  const trimmed = value.trim();
  if (!trimmed) return {};
  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed) as unknown;
  } catch {
    throw new Error(t.apiMap.invalidJsonSchema);
  }
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error(t.apiMap.invalidJsonSchema);
  }
  return parsed as Record<string, unknown>;
}

function readErrorMessage(exc: unknown, fallback: string): string {
  if (!(exc instanceof Error)) return fallback;
  try {
    const parsed = JSON.parse(exc.message) as { detail?: string };
    return parsed.detail || exc.message;
  } catch {
    return exc.message || fallback;
  }
}
