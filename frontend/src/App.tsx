import { useEffect, useMemo, useState } from "react";

import { listProjects } from "./api/projects";
import { AppLayout } from "./components/layout/AppLayout";
import { getInitialLanguage, messages, persistLanguage, type Language } from "./i18n";
import { ApiMap } from "./pages/ApiMap";
import { Dashboard } from "./pages/Dashboard";
import { DatabaseMap } from "./pages/DatabaseMap";
import { ProjectSetup } from "./pages/ProjectSetup";
import { Reports } from "./pages/Reports";
import { Settings } from "./pages/Settings";
import { TestRunner } from "./pages/TestRunner";
import type { PageKey } from "./types/navigation";
import type { ProjectListItem } from "./types/project";

export default function App() {
  const [activePage, setActivePage] = useState<PageKey>("dashboard");
  const [language, setLanguage] = useState<Language>(() => getInitialLanguage());
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [selectedEndpointForTestId, setSelectedEndpointForTestId] = useState<number | null>(null);
  const t = messages[language];

  async function refreshProjects() {
    try {
      const projectList = await listProjects();
      setProjects(projectList);
      setSelectedProjectId((current) => current ?? projectList[0]?.id ?? null);
    } catch {
      setProjects([]);
    }
  }

  useEffect(() => {
    void refreshProjects();
  }, []);

  function changeLanguage(nextLanguage: Language) {
    setLanguage(nextLanguage);
    persistLanguage(nextLanguage);
  }

  const page = useMemo(() => {
    const commonProps = {
      t,
      projects,
      selectedProjectId,
      onNavigate: setActivePage,
      onProjectsChanged: refreshProjects
    };

    switch (activePage) {
      case "setup":
        return <ProjectSetup {...commonProps} onProjectSelected={setSelectedProjectId} />;
      case "apiMap":
        return <ApiMap {...commonProps} onEndpointTestSelected={setSelectedEndpointForTestId} />;
      case "databaseMap":
        return <DatabaseMap {...commonProps} />;
      case "testRunner":
        return <TestRunner {...commonProps} initialEndpointId={selectedEndpointForTestId} />;
      case "reports":
        return <Reports t={t} />;
      case "settings":
        return <Settings language={language} onLanguageChange={changeLanguage} t={t} />;
      case "dashboard":
      default:
        return <Dashboard {...commonProps} />;
    }
  }, [activePage, language, projects, selectedEndpointForTestId, selectedProjectId, t]);

  return (
    <AppLayout
      activePage={activePage}
      language={language}
      onLanguageChange={changeLanguage}
      onNavigate={setActivePage}
      onProjectChange={setSelectedProjectId}
      projects={projects}
      selectedProjectId={selectedProjectId}
      t={t}
    >
      {page}
    </AppLayout>
  );
}
