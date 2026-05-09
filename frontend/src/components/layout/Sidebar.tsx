import {
  BarChart3,
  Box,
  CirclePlay,
  Database,
  FileText,
  Home,
  Network,
  PanelLeftClose,
  Settings,
  TerminalSquare
} from "lucide-react";

import type { Messages } from "../../i18n";
import type { PageKey } from "../../types/navigation";

interface SidebarProps {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
  t: Messages;
}

const navItems = [
  { key: "dashboard", icon: Home },
  { key: "setup", icon: Box },
  { key: "apiMap", icon: Network },
  { key: "databaseMap", icon: Database },
  { key: "testRunner", icon: CirclePlay },
  { key: "reports", icon: BarChart3 },
  { key: "settings", icon: Settings }
] as const;

export function Sidebar({ activePage, onNavigate, t }: SidebarProps) {
  return (
    <aside className="app-sidebar">
      <div className="brand-block">
        <div className="brand-logo">
          <Network size={26} />
        </div>
        <div>
          <strong>{t.common.appName}</strong>
          <span>{t.common.tagline}</span>
        </div>
      </div>

      <nav className="side-nav" aria-label="Primary navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          const label = navLabel(item.key, t);
          return (
            <button
              className={activePage === item.key ? "side-nav-item active" : "side-nav-item"}
              key={item.key}
              onClick={() => onNavigate(item.key)}
              type="button"
            >
              <Icon size={20} />
              <span>{label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="agent-card-mini">
          <div className="terminal-icon">
            <TerminalSquare size={20} />
          </div>
          <div>
            <strong>Local Agent</strong>
            <span>
              <i /> v1.2.3
            </span>
          </div>
          <FileText size={16} />
        </div>
        <button className="collapse-button" type="button">
          <PanelLeftClose size={18} />
          {t.nav.collapse}
        </button>
      </div>
    </aside>
  );
}

function navLabel(page: PageKey, t: Messages): string {
  const labels: Record<PageKey, string> = {
    dashboard: t.nav.dashboard,
    setup: t.nav.projectSetup,
    apiMap: t.nav.apiMap,
    databaseMap: t.nav.databaseMap,
    testRunner: t.nav.testRunner,
    reports: t.nav.reports,
    settings: t.nav.settings
  };
  return labels[page];
}
