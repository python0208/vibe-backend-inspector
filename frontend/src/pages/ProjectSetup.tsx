import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { Database, FileJson, FolderOpen, PlayCircle, Plus, Save, Trash2 } from "lucide-react";

import { testDatabase, testOpenApi } from "../api/connectionTests";
import { createProject, deleteProject, getProject, updateProject } from "../api/projects";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatusBadge } from "../components/ui/StatusBadge";
import type { Messages } from "../i18n";
import type {
  AuthConfig,
  AuthType,
  ConnectionTestResult,
  DatabaseType,
  Project,
  ProjectListItem,
  ProjectPayload
} from "../types/project";

const emptyAuth: AuthConfig = { type: "none", headers: {} };

const initialForm: ProjectPayload = {
  name: "",
  project_path: "",
  service_base_url: "http://localhost:8000",
  openapi_url: "http://localhost:8000/openapi.json",
  database_type: "none",
  database_config: {},
  auth_config: emptyAuth
};

type StatusState = "idle" | "checking" | "success" | "error";

interface ProjectSetupProps {
  t: Messages;
  projects: ProjectListItem[];
  selectedProjectId: number | null;
  onProjectSelected: (projectId: number | null) => void;
  onProjectsChanged: () => Promise<void>;
}

export function ProjectSetup({
  t,
  projects,
  selectedProjectId,
  onProjectSelected,
  onProjectsChanged
}: ProjectSetupProps) {
  const [selectedId, setSelectedId] = useState<number | null>(selectedProjectId);
  const [form, setForm] = useState<ProjectPayload>(initialForm);
  const [message, setMessage] = useState<string | null>(null);
  const [openApiResult, setOpenApiResult] = useState<ConnectionTestResult | null>(null);
  const [databaseResult, setDatabaseResult] = useState<ConnectionTestResult | null>(null);
  const [openApiState, setOpenApiState] = useState<StatusState>("idle");
  const [databaseState, setDatabaseState] = useState<StatusState>("idle");

  useEffect(() => {
    if (selectedProjectId && selectedProjectId !== selectedId) {
      void loadProject(selectedProjectId);
    }
  }, [selectedProjectId]);

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedId),
    [projects, selectedId]
  );

  async function loadProject(id: number) {
    const project = await getProject(id);
    setSelectedId(id);
    onProjectSelected(id);
    setForm(fromProject(project));
    setOpenApiResult(null);
    setDatabaseResult(null);
    setOpenApiState("idle");
    setDatabaseState("idle");
    setMessage(null);
  }

  function startNewProject() {
    setSelectedId(null);
    onProjectSelected(null);
    setForm(initialForm);
    setMessage(null);
    setOpenApiResult(null);
    setDatabaseResult(null);
    setOpenApiState("idle");
    setDatabaseState("idle");
  }

  function updateField(field: keyof ProjectPayload, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function updateDatabaseType(value: DatabaseType) {
    setForm((current) => ({
      ...current,
      database_type: value,
      database_config: defaultDatabaseConfig(value)
    }));
    setDatabaseResult(null);
    setDatabaseState("idle");
  }

  function updateDatabaseConfig(field: string, value: string) {
    setForm((current) => ({
      ...current,
      database_config: {
        ...current.database_config,
        [field]: field === "port" && value ? Number(value) : value
      }
    }));
  }

  function updateAuthType(value: AuthType) {
    setForm((current) => ({
      ...current,
      auth_config: { type: value, headers: {} }
    }));
  }

  function updateAuthConfig(field: keyof AuthConfig, value: string) {
    setForm((current) => ({
      ...current,
      auth_config: {
        ...current.auth_config,
        [field]: value
      }
    }));
  }

  function updateHeaders(value: string) {
    const headers: Record<string, string> = {};
    value
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .forEach((line) => {
        const [key, ...rest] = line.split(":");
        if (key && rest.length > 0) {
          headers[key.trim()] = rest.join(":").trim();
        }
      });

    setForm((current) => ({
      ...current,
      auth_config: {
        ...current.auth_config,
        headers
      }
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);

    const payload = normalizePayload(form);
    const saved = selectedId ? await updateProject(selectedId, payload) : await createProject(payload);
    setSelectedId(saved.id);
    onProjectSelected(saved.id);
    setForm(fromProject(saved));
    await onProjectsChanged();
    setMessage(t.projectSetup.savedMessage);
  }

  async function handleDelete() {
    if (!selectedId) {
      return;
    }
    await deleteProject(selectedId);
    await onProjectsChanged();
    startNewProject();
    setMessage(t.projectSetup.deletedMessage);
  }

  async function handleOpenApiTest() {
    if (!form.openapi_url) {
      setOpenApiResult({ ok: false, message: t.projectSetup.openApiRequired });
      setOpenApiState("error");
      return;
    }
    setOpenApiState("checking");
    const result = await testOpenApi(form.openapi_url);
    setOpenApiResult(result);
    setOpenApiState(result.ok ? "success" : "error");
  }

  async function handleDatabaseTest() {
    setDatabaseState("checking");
    const result = await testDatabase(form.database_type, normalizePayload(form).database_config);
    setDatabaseResult(result);
    setDatabaseState(result.ok ? "success" : "error");
  }

  return (
    <form className="page-stack" onSubmit={(event) => void handleSubmit(event)}>
      <PageHeader
        actions={
          <div className="button-row">
            <button className="ghost-button" onClick={startNewProject} type="button">
              <Plus size={17} />
              {t.common.new}
            </button>
            <button className="primary-button" type="submit">
              <Save size={17} />
              {t.projectSetup.saveConfig}
            </button>
          </div>
        }
        subtitle={t.projectSetup.subtitle}
        title={t.projectSetup.title}
      />

      <div className="setup-layout">
        <div className="setup-main">
          <StepRail t={t} />
          {message ? <div className="notice success">{message}</div> : null}

          <Card>
            <SectionHeading icon={FolderOpen} title={t.projectSetup.basicInfo} />
            <div className="form-grid two">
              <Field label={t.projectSetup.projectName} required>
                <input value={form.name} onChange={(event) => updateField("name", event.target.value)} required />
              </Field>
              <Field label={t.projectSetup.projectDirectory} required>
                <input
                  value={form.project_path}
                  onChange={(event) => updateField("project_path", event.target.value)}
                  required
                />
              </Field>
            </div>
          </Card>

          <Card>
            <SectionHeading icon={FileJson} title={t.projectSetup.serviceAndOpenApi} />
            <div className="form-grid two">
              <Field label={t.projectSetup.serviceBaseUrl} required>
                <input
                  value={form.service_base_url}
                  onChange={(event) => updateField("service_base_url", event.target.value)}
                  required
                />
              </Field>
              <Field label={t.projectSetup.openApiUrl}>
                <div className="input-action">
                  <input
                    value={form.openapi_url ?? ""}
                    onChange={(event) => updateField("openapi_url", event.target.value)}
                  />
                  <button className="ghost-button compact" onClick={() => void handleOpenApiTest()} type="button">
                    {t.projectSetup.testOpenApi}
                  </button>
                </div>
              </Field>
            </div>
          </Card>

          <div className="setup-two-columns">
            <Card>
              <SectionHeading icon={Database} title={t.projectSetup.databaseConfiguration} />
              <Field label={t.projectSetup.databaseType}>
                <div className="segmented-control">
                  {(["none", "sqlite", "mysql", "postgres"] as DatabaseType[]).map((type) => (
                    <button
                      className={form.database_type === type ? "active" : ""}
                      key={type}
                      onClick={() => updateDatabaseType(type)}
                      type="button"
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </Field>
              <DatabaseFields
                config={form.database_config}
                databaseType={form.database_type}
                onChange={updateDatabaseConfig}
                t={t}
              />
              <button className="outline-button full-width" onClick={() => void handleDatabaseTest()} type="button">
                <PlayCircle size={17} />
                {t.projectSetup.testDatabase}
              </button>
            </Card>

            <Card>
              <SectionHeading icon={FileJson} title={t.projectSetup.authentication} />
              <Field label={t.projectSetup.authType}>
                <div className="segmented-control">
                  {(["none", "bearer", "basic", "custom_headers"] as AuthType[]).map((type) => (
                    <button
                      className={form.auth_config.type === type ? "active" : ""}
                      key={type}
                      onClick={() => updateAuthType(type)}
                      type="button"
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </Field>
              <AuthFields
                authConfig={form.auth_config}
                onAuthChange={updateAuthConfig}
                onHeadersChange={updateHeaders}
                t={t}
              />
            </Card>
          </div>
        </div>

        <aside className="setup-aside">
          <Card>
            <div className="card-heading">
              <div>
                <h2>{t.projectSetup.projectSummary}</h2>
                <p>{t.projectSetup.useTestDatabase}</p>
              </div>
            </div>
            <div className="summary-table">
              <SummaryRow label={t.projectSetup.projectName} value={form.name || "-"} />
              <SummaryRow label={t.projectSetup.projectDirectory} value={form.project_path || "-"} />
              <SummaryRow label={t.projectSetup.serviceBaseUrl} value={form.service_base_url || "-"} />
              <SummaryRow label={t.projectSetup.databaseType} value={form.database_type} />
            </div>
          </Card>

          <Card>
            <div className="card-heading">
              <div>
                <h2>{t.projectSetup.connectionStatus}</h2>
                <p>{t.common.phaseNotice}</p>
              </div>
            </div>
            <div className="status-list">
              <ConnectionRow label={t.projectSetup.backendReachable} state="idle" t={t} />
              <ConnectionRow
                label={t.projectSetup.openApiFound}
                message={openApiResult?.title ?? openApiResult?.message}
                state={openApiState}
                t={t}
              />
              <ConnectionRow
                label={t.projectSetup.databaseConnected}
                message={databaseResult?.message}
                state={databaseState}
                t={t}
              />
            </div>
          </Card>

          <Card>
            <div className="card-heading">
              <div>
                <h2>{t.projectSetup.savedProjects}</h2>
                <p>{projects.length} total</p>
              </div>
            </div>
            <div className="project-list-modern">
              {projects.length === 0 ? (
                <div className="empty-panel">{t.projectSetup.noSavedProjects}</div>
              ) : (
                projects.map((project) => (
                  <button
                    className={project.id === selectedId ? "saved-project active" : "saved-project"}
                    key={project.id}
                    onClick={() => void loadProject(project.id)}
                    type="button"
                  >
                    <strong>{project.name}</strong>
                    <span>{project.database_type}</span>
                  </button>
                ))
              )}
            </div>
          </Card>

          {selectedId ? (
            <button className="danger-button full-width" onClick={() => void handleDelete()} type="button">
              <Trash2 size={17} />
              {t.projectSetup.deleteProject}
            </button>
          ) : null}
        </aside>
      </div>
    </form>
  );
}

function StepRail({ t }: { t: Messages }) {
  const steps = [
    t.projectSetup.basicInfo,
    t.projectSetup.serviceAndOpenApi,
    t.projectSetup.databaseConfiguration,
    t.projectSetup.authentication
  ];
  return (
    <Card className="step-rail">
      {steps.map((step, index) => (
        <div className={index === 0 ? "step-pill active" : "step-pill"} key={step}>
          <span>{index + 1}</span>
          <strong>{step}</strong>
        </div>
      ))}
    </Card>
  );
}

function SectionHeading({ icon: Icon, title }: { icon: typeof FolderOpen; title: string }) {
  return (
    <div className="section-heading">
      <div className="section-icon">
        <Icon size={17} />
      </div>
      <h2>{title}</h2>
    </div>
  );
}

function Field({ children, label, required = false }: { children: React.ReactNode; label: string; required?: boolean }) {
  return (
    <label className="form-field">
      <span>
        {label}
        {required ? <em>*</em> : null}
      </span>
      {children}
    </label>
  );
}

function DatabaseFields({
  config,
  databaseType,
  onChange,
  t
}: {
  config: Record<string, unknown>;
  databaseType: DatabaseType;
  onChange: (field: string, value: string) => void;
  t: Messages;
}) {
  if (databaseType === "none") {
    return <div className="empty-panel compact">{t.projectSetup.noDatabase}</div>;
  }

  if (databaseType === "sqlite") {
    return (
      <div className="form-grid one">
        <Field label={t.projectSetup.sqlitePath}>
          <input
            value={String(config.database_path ?? "")}
            onChange={(event) => onChange("database_path", event.target.value)}
          />
        </Field>
      </div>
    );
  }

  return (
    <div className="form-grid two compact-grid">
      <Field label={t.projectSetup.host}>
        <input value={String(config.host ?? "")} onChange={(event) => onChange("host", event.target.value)} />
      </Field>
      <Field label={t.projectSetup.port}>
        <input value={String(config.port ?? "")} onChange={(event) => onChange("port", event.target.value)} />
      </Field>
      <Field label={t.projectSetup.databaseName}>
        <input
          value={String(config.database ?? "")}
          onChange={(event) => onChange("database", event.target.value)}
        />
      </Field>
      <Field label={t.projectSetup.username}>
        <input
          value={String(config.username ?? "")}
          onChange={(event) => onChange("username", event.target.value)}
        />
      </Field>
      <Field label={t.projectSetup.password}>
        <input
          type="password"
          value={String(config.password ?? "")}
          onChange={(event) => onChange("password", event.target.value)}
        />
      </Field>
    </div>
  );
}

function AuthFields({
  authConfig,
  onAuthChange,
  onHeadersChange,
  t
}: {
  authConfig: AuthConfig;
  onAuthChange: (field: keyof AuthConfig, value: string) => void;
  onHeadersChange: (value: string) => void;
  t: Messages;
}) {
  if (authConfig.type === "none") {
    return <div className="empty-panel compact">{t.projectSetup.noAuth}</div>;
  }

  if (authConfig.type === "bearer") {
    return (
      <div className="form-grid one">
        <Field label={t.projectSetup.bearerToken}>
          <input
            type="password"
            value={authConfig.token ?? ""}
            onChange={(event) => onAuthChange("token", event.target.value)}
          />
        </Field>
      </div>
    );
  }

  if (authConfig.type === "basic") {
    return (
      <div className="form-grid two">
        <Field label={t.projectSetup.username}>
          <input
            value={authConfig.username ?? ""}
            onChange={(event) => onAuthChange("username", event.target.value)}
          />
        </Field>
        <Field label={t.projectSetup.password}>
          <input
            type="password"
            value={authConfig.password ?? ""}
            onChange={(event) => onAuthChange("password", event.target.value)}
          />
        </Field>
      </div>
    );
  }

  return (
    <div className="form-grid one">
      <Field label={t.projectSetup.customHeaders}>
        <textarea
          onChange={(event: ChangeEvent<HTMLTextAreaElement>) => onHeadersChange(event.target.value)}
          placeholder="X-Api-Key: test-key"
          value={Object.entries(authConfig.headers ?? {})
            .map(([key, value]) => `${key}: ${value}`)
            .join("\n")}
        />
      </Field>
    </div>
  );
}

function ConnectionRow({
  label,
  message,
  state,
  t
}: {
  label: string;
  message?: string;
  state: StatusState;
  t: Messages;
}) {
  const tone = state === "success" ? "success" : state === "error" ? "danger" : state === "checking" ? "warning" : "neutral";
  const text = {
    idle: t.common.idle,
    checking: t.common.checking,
    success: t.common.success,
    error: t.common.error
  }[state];

  return (
    <div className="connection-row">
      <div>
        <strong>{label}</strong>
        {message ? <span>{message}</span> : null}
      </div>
      <StatusBadge tone={tone}>{text}</StatusBadge>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="summary-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function defaultDatabaseConfig(databaseType: DatabaseType): Record<string, unknown> {
  if (databaseType === "sqlite") {
    return { database_path: "" };
  }
  if (databaseType === "mysql") {
    return { host: "localhost", port: 3306, database: "", username: "", password: "" };
  }
  if (databaseType === "postgres") {
    return { host: "localhost", port: 5432, database: "", username: "", password: "" };
  }
  return {};
}

function normalizePayload(payload: ProjectPayload): ProjectPayload {
  return {
    ...payload,
    openapi_url: payload.openapi_url || null,
    database_config: payload.database_type === "none" ? {} : payload.database_config,
    auth_config: payload.auth_config.type === "none" ? emptyAuth : payload.auth_config
  };
}

function fromProject(project: Project): ProjectPayload {
  return {
    name: project.name,
    project_path: project.project_path,
    service_base_url: project.service_base_url,
    openapi_url: project.openapi_url ?? "",
    database_type: project.database_type,
    database_config: project.database_config ?? defaultDatabaseConfig(project.database_type),
    auth_config: project.auth_config ?? emptyAuth
  };
}
