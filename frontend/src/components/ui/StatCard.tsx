import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface StatCardProps {
  icon: LucideIcon;
  title: string;
  value: ReactNode;
  hint?: string;
  tone?: "blue" | "purple" | "cyan" | "green" | "orange" | "red";
}

export function StatCard({ icon: Icon, title, value, hint, tone = "blue" }: StatCardProps) {
  return (
    <CardlessStat tone={tone}>
      <div className={`stat-icon ${tone}`}>
        <Icon size={24} />
      </div>
      <div>
        <span>{title}</span>
        <strong>{value}</strong>
        {hint ? <p>{hint}</p> : null}
      </div>
    </CardlessStat>
  );
}

function CardlessStat({ children, tone }: { children: ReactNode; tone: string }) {
  return <article className={`stat-card tone-${tone}`}>{children}</article>;
}
