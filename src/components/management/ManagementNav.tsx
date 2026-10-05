import { Link, useRouterState } from "@tanstack/react-router";
import { useI18n } from "../../i18n/context";
import type { TranslationKey } from "../../i18n/catalog";

const managementLinks = [
  { to: "/management", label: "management.overviewNav" },
  { to: "/management/pillars", label: "management.pillarsNav" },
  { to: "/management/attention", label: "management.attentionNav" },
  { to: "/management/adherence", label: "management.adherenceNav" },
  { to: "/management/voice", label: "management.voiceNav" },
] as const;

export function ManagementNav() {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const { t } = useI18n();

  return (
    <nav className="management-nav" aria-label={t("management.navAria")}>
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
              {t(item.label)}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export function ManagementLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="management-layout">
      <ManagementNav />
      {children}
    </div>
  );
}

export function ManagementPageTitle({
  eyebrow,
  statusBadge,
  statusTone = "active",
  title,
  description,
}: {
  eyebrow?: TranslationKey;
  statusBadge?: string;
  statusTone?: "active" | "neutral";
  title: string;
  description: string;
}) {
  const { t } = useI18n();
  return (
    <header className="management-page-title">
      <p className="management-eyebrow">{t(eyebrow ?? "management.eyebrow")}</p>
      {statusBadge && <span className={`management-status management-status--${statusTone}`}>{statusBadge}</span>}
      <h1>{title}</h1>
      <p>{description}</p>
    </header>
  );
}
