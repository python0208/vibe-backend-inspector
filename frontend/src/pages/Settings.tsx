import type { Language, Messages } from "../i18n";
import { LanguageToggle } from "../components/layout/LanguageToggle";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatusBadge } from "../components/ui/StatusBadge";

export function Settings({
  language,
  onLanguageChange,
  t
}: {
  language: Language;
  onLanguageChange: (language: Language) => void;
  t: Messages;
}) {
  return (
    <section className="page-stack">
      <PageHeader subtitle={t.placeholders.settingsSubtitle} title={t.placeholders.settingsTitle} />
      <Card>
        <div className="card-heading">
          <div>
            <h2>Language</h2>
            <p>{t.common.searchPlaceholder}</p>
          </div>
          <LanguageToggle language={language} onChange={onLanguageChange} />
        </div>
      </Card>
      <Card>
        <div className="card-heading">
          <div>
            <h2>Local Agent</h2>
            <p>{t.placeholders.staticOnly}</p>
          </div>
          <StatusBadge tone="success">{t.common.localAgentOnline}</StatusBadge>
        </div>
      </Card>
    </section>
  );
}
