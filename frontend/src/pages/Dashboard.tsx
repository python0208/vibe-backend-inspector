import { Activity, Clock3, Database, FileJson, RefreshCw, Server, Settings2 } from "lucide-react";
import { useEffect, useState } from "react";

import { API_BASE_URL } from "../api/client";
import { getHealth } from "../api/health";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/ui/StatCard";
import { StatusBadge } from "../components/ui/StatusBadge";
import type { Messages } from "../i18n";
import type { PageKey } from "../types/navigation";
import type { ProjectListItem } from "../types/project";

interface DashboardProps {
  t: Messages;
  projects: ProjectListItem[];
  selectedProjectId: number | null;
  onNavigate: (page: PageKey) => void;
  onProjectsChanged: () => Promise<void>;
}

export function Dashboard({ t, projects, selectedProjectId, onNavigate, onProjectsChanged }: DashboardProps) {
  const [connected, setConnected] = useState(false);
  const [healthText, setHealthText] = useState(API_BASE_URL);
  const [checking, setChecking] = useState(true);

  async function refresh() {
    setChecking(true);
    try {
      const health = await getHealth();
      await onProjectsChanged();
      setConnected(true);
      setHealthText(`${health.app} ${health.version}`);
    } catch (exc) {
      setConnected(false);
      setHealthText(exc instanceof Error ? exc.message : API_BASE_URL);
    } finally {
      setChecking(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const selectedProject =
    projects.find((project) => project.id === selectedProjectId) ?? projects[0] ?? null;

  return (
    <section className="page-stack">
      <PageHeader
        actions={
          <button className="ghost-button" onClick={() => void refresh()} type="button">
            <RefreshCw size={17} />
            {t.common.refresh}
          </button>
        }
        subtitle={t.dashboard.subtitle}
        title={t.dashboard.title}
      />

      <div className="stat-grid four">
        <StatCard
          hint={healthText}
          icon={Server}
          title={t.dashboard.backend}
          tone="blue"
          value={checking ? t.common.checking : connected ? t.common.connected : t.common.disconnected}
        />
        <StatCard
          hint="SQLite local state"
          icon={Database}
          title={t.dashboard.savedProjects}
          tone="purple"
          value={projects.length}
        />
        <StatCard
          hint={t.common.phaseNotice}
          icon={Activity}
          title={t.dashboard.currentScope}
          tone="cyan"
          value={t.dashboard.configurationOnly}
        />
        <StatCard
          hint={new Date().toLocaleTimeString()}
          icon={Clock3}
          title={t.dashboard.lastCheck}
          tone="green"
          value={checking ? "..." : "Now"}
        />
      </div>

      <Card>
        <div className="card-heading">
          <div>
            <h2>{t.dashboard.serviceStatus}</h2>
            <p>{connected ? t.common.connected : t.common.disconnected}</p>
          </div>
          <StatusBadge tone={connected ? "success" : "danger"}>
            {connected ? t.common.connected : t.common.disconnected}
          </StatusBadge>
        </div>

        <div className="service-grid">
          <ServiceTile
            icon={Server}
            label={t.dashboard.backend}
            meta={healthText}
            status={connected ? t.common.connected : t.common.disconnected}
            tone={connected ? "success" : "danger"}
          />
          <ServiceTile
            icon={FileJson}
            label="OpenAPI Docs"
            meta={selectedProject?.openapi_url ?? t.common.noProject}
            status={selectedProject?.openapi_url ? t.common.idle : t.common.noProject}
            tone={selectedProject?.openapi_url ? "info" : "neutral"}
          />
          <ServiceTile
            icon={Database}
            label="Database"
            meta={selectedProject?.database_type ?? "none"}
            status={selectedProject ? t.common.idle : t.common.noProject}
            tone={selectedProject ? "info" : "neutral"}
          />
        </div>
      </Card>

      <div className="dashboard-lower-grid">
        <Card>
          <div className="card-heading">
            <div>
              <h2>{t.dashboard.latestProject}</h2>
              <p>{t.dashboard.latestProjectHint}</p>
            </div>
            <button className="primary-button" onClick={() => onNavigate("setup")} type="button">
              <Settings2 size={17} />
              {t.dashboard.openSetup}
            </button>
          </div>

          {selectedProject ? (
            <div className="summary-table">
              <SummaryRow label={t.projectSetup.projectName} value={selectedProject.name} />
              <SummaryRow label={t.projectSetup.projectDirectory} value={selectedProject.project_path} />
              <SummaryRow label={t.projectSetup.serviceBaseUrl} value={selectedProject.service_base_url} />
              <SummaryRow label={t.projectSetup.databaseType} value={selectedProject.database_type} />
            </div>
          ) : (
            <div className="empty-panel">{t.dashboard.emptyProject}</div>
          )}
        </Card>

        <Card>
          <div className="card-heading">
            <div>
              <h2>{t.dashboard.quickActions}</h2>
              <p>{t.common.phaseNotice}</p>
            </div>
          </div>
          <div className="quick-action-grid">
            <button className="quick-action blue" onClick={() => onNavigate("setup")} type="button">
              <Settings2 size={22} />
              <span>{t.dashboard.configureProject}</span>
            </button>
            <button className="quick-action purple" onClick={() => onNavigate("setup")} type="button">
              <FileJson size={22} />
              <span>{t.dashboard.validateOpenApi}</span>
            </button>
            <button className="quick-action cyan" onClick={() => onNavigate("setup")} type="button">
              <Database size={22} />
              <span>{t.dashboard.testDatabase}</span>
            </button>
          </div>
        </Card>
      </div>
    </section>
  );
}

function ServiceTile({
  icon: Icon,
  label,
  meta,
  status,
  tone
}: {
  icon: typeof Server;
  label: string;
  meta: string;
  status: string;
  tone: "success" | "danger" | "info" | "neutral";
}) {
  return (
    <div className="service-tile">
      <div className="service-icon">
        <Icon size={24} />
      </div>
      <div>
        <strong>{label}</strong>
        <span>{meta}</span>
      </div>
      <StatusBadge tone={tone}>{status}</StatusBadge>
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
