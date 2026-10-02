import { Link, useRouterState } from "@tanstack/react-router";
import { ManagementFiltersBar } from "./ManagementFilters";

const managementLinks = [
  { to: "/management", label: "Visão Geral" },
  { to: "/management/pillars", label: "Pilares" },
  { to: "/management/attention", label: "Pontos de Atenção" },
  { to: "/management/adherence", label: "Adesão" },
  { to: "/management/voice", label: "Sua Voz" },
  { to: "/management/action-plans", label: "Planos de Ação" },
] as const;

export function ManagementNav() {
  const pathname = useRouterState({ select: (state) => state.location.pathname });

  return (
    <nav className="management-nav" aria-label="Navegação da gestão">
      <div className="management-nav__links">
        {managementLinks.map((item) => {
          const active = pathname === item.to;
          return (
            <Link
              key={item.to}
              className={`management-nav__link${active ? " is-active" : ""}`}
              to={item.to}
              aria-current={active ? "page" : undefined}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export function ManagementLayout({ children, showDemoFilters = true }: { children: React.ReactNode; showDemoFilters?: boolean }) {
  return (
    <div className="management-layout">
      <ManagementNav />
      {showDemoFilters && <ManagementFiltersBar />}
      {children}
    </div>
  );
}

export function ManagementPageTitle({
  eyebrow = "VISÃO DA GESTÃO",
  statusBadge,
  title,
  description,
}: {
  eyebrow?: string;
  statusBadge?: string;
  title: string;
  description: string;
}) {
  return (
    <header className="management-page-title">
      <p className="management-eyebrow">{eyebrow}</p>
      {statusBadge && <span className="management-status">{statusBadge}</span>}
      <h1>{title}</h1>
      <p>{description}</p>
    </header>
  );
}
