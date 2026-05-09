import { AlertTriangle, BarChart3, Database, FileText, ShieldCheck, XCircle } from "lucide-react";

import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/ui/StatCard";
import { StatusBadge } from "../components/ui/StatusBadge";
import type { Messages } from "../i18n";

export function Reports({ t }: { t: Messages }) {
  return (
    <section className="page-stack">
      <PageHeader
        actions={<div className="button-row"><button className="ghost-button" type="button">Export Markdown</button><button className="primary-button" type="button">Share Report</button></div>}
        subtitle={t.placeholders.reportsSubtitle}
        title={t.placeholders.reportsTitle}
      />
      <div className="stat-grid five">
        <StatCard icon={BarChart3} title="Endpoints Tested" value="128" hint={t.common.phaseNotice} tone="blue" />
        <StatCard icon={ShieldCheck} title="Passed" value="105" hint={t.common.phaseNotice} tone="green" />
        <StatCard icon={XCircle} title="Failed" value="23" hint={t.common.phaseNotice} tone="red" />
        <StatCard icon={Database} title="Database Changes" value="36" hint={t.common.phaseNotice} tone="purple" />
        <StatCard icon={AlertTriangle} title="Risk Score" value="62/100" hint="Medium Risk" tone="orange" />
      </div>
      <div className="reports-grid">
        <Card><h2>Overall Score</h2><div className="score-big">82<span>/100</span></div><StatusBadge tone="success">Good</StatusBadge><p>{t.placeholders.staticOnly}</p></Card>
        <Card><h2>Highlights</h2><div className="highlight-row"><XCircle size={18} />Severe Issues <strong>23</strong></div><div className="highlight-row"><AlertTriangle size={18} />Warnings <strong>14</strong></div><div className="highlight-row"><FileText size={18} />Recommendations <strong>7</strong></div></Card>
        <Card><h2>Failed Endpoints</h2><table className="data-table"><tbody>{["POST /api/orders/create", "GET /api/users/{id}", "PUT /api/products/{id}"].map((item) => <tr key={item}><td>{item}</td><td><StatusBadge tone="danger">500</StatusBadge></td></tr>)}</tbody></table></Card>
      </div>
    </section>
  );
}
