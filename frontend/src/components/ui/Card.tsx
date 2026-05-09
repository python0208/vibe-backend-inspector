import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className = "" }: CardProps) {
  return <section className={`vbi-card ${className}`.trim()}>{children}</section>;
}
