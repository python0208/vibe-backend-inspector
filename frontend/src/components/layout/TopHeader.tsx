import { BriefcaseBusiness, ChevronDown, Command, Search, UserRound } from "lucide-react";

import type { Language, Messages } from "../../i18n";
import type { ProjectListItem } from "../../types/project";
import { LanguageToggle } from "./LanguageToggle";

interface TopHeaderProps {
  projects: ProjectListItem[];
  selectedProjectId: number | null;
  onProjectChange: (projectId: number | null) => void;
  language: Language;
  onLanguageChange: (language: Language) => void;
  t: Messages;
}

export function TopHeader({
  projects,
  selectedProjectId,
  onProjectChange,
  language,
  onLanguageChange,
  t
}: TopHeaderProps) {
  const selectedProject = projects.find((project) => project.id === selectedProjectId) ?? projects[0];

  return (
    <header className="top-header">
      <div className="project-picker">
        <BriefcaseBusiness size={18} />
        <select
          aria-label="Project selector"
          onChange={(event) => onProjectChange(event.target.value ? Number(event.target.value) : null)}
          value={selectedProject?.id ?? ""}
        >
          <option value="">{t.common.noProject}</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
        <ChevronDown size={16} />
      </div>

      <label className="global-search">
        <Search size={19} />
        <input placeholder={t.common.searchPlaceholder} />
        <span>
          <Command size={14} />K
        </span>
      </label>

      <div className="header-actions">
        <div className="agent-online">
          <span />
          <strong>{t.common.localAgentOnline}</strong>
        </div>
        <LanguageToggle language={language} onChange={onLanguageChange} />
        <button className="user-menu" type="button">
          <span className="avatar">
            <UserRound size={19} />
          </span>
          {t.common.userName}
          <ChevronDown size={16} />
        </button>
      </div>
    </header>
  );
}
