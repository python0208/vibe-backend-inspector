import { Network, Play, RefreshCw, Search, ShieldCheck, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { autoDetectOpenApi, discoverOpenApi, listEndpoints } from "../api/endpoints";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/ui/StatCard";
import { StatusBadge, type StatusTone } from "../components/ui/StatusBadge";
import type { Messages } from "../i18n";
import type { Endpoint, HttpMethod } from "../types/api";
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
  const [loading, setLoading] = useState(false);
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

  const filteredEndpoints = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return endpoints.filter((endpoint) => {
      const matchesSearch =
        !normalizedSearch ||
        endpoint.path.toLowerCase().includes(normalizedSearch) ||
        (endpoint.summary ?? "").toLowerCase().includes(normalizedSearch);
      const matchesMethod = methodFilter === "ALL" || endpoint.method === methodFilter;
      const matchesStatus = statusFilter === "ALL" || endpoint.test_status === statusFilter;
      return matchesSearch && matchesMethod && matchesStatus;
    });
  }, [endpoints, methodFilter, search, statusFilter]);

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
          <button className="primary-button" disabled={loading} onClick={() => void syncOpenApi()} type="button">
            <RefreshCw size={17} />
            {selectedProject.openapi_url ? t.apiMap.syncOpenApi : t.apiMap.autoDetectOpenApi}
          </button>
        }
        subtitle={t.placeholders.apiMapSubtitle}
        title={t.placeholders.apiMapTitle}
      />

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
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <EndpointDetail endpoint={selectedEndpoint} t={t} />
      </div>
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
          <DetailRow label="Source" value={endpoint.source} />
        </div>
        <SchemaBlock title={t.apiMap.queryParams} value={endpoint.query_params} />
        <SchemaBlock title={t.apiMap.pathParams} value={endpoint.path_params} />
        <SchemaBlock title={t.apiMap.requestSchema} value={endpoint.request_body_schema} />
        <SchemaBlock title={t.apiMap.responseSchema} value={endpoint.response_schema} />
      </div>
    </Card>
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
