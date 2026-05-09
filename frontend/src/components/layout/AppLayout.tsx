import type { ReactNode } from "react";

import type { Language, Messages } from "../../i18n";
import type { PageKey } from "../../types/navigation";
import type { ProjectListItem } from "../../types/project";
import { Sidebar } from "./Sidebar";
import { TopHeader } from "./TopHeader";

interface AppLayoutProps {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
  projects: ProjectListItem[];
  selectedProjectId: number | null;
  onProjectChange: (projectId: number | null) => void;
  language: Language;
  onLanguageChange: (language: Language) => void;
  t: Messages;
  children: ReactNode;
}

export function AppLayout({
  activePage,
  onNavigate,
  projects,
  selectedProjectId,
  onProjectChange,
  language,
  onLanguageChange,
  t,
  children
}: AppLayoutProps) {
  return (
    <div className="app-frame">
      <Sidebar activePage={activePage} onNavigate={onNavigate} t={t} />
      <div className="app-workspace">
        <TopHeader
          language={language}
          onLanguageChange={onLanguageChange}
          onProjectChange={onProjectChange}
          projects={projects}
          selectedProjectId={selectedProjectId}
          t={t}
        />
        <main className="main-content">{children}</main>
      </div>
    </div>
  );
}
