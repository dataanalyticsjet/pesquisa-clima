import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { MetricCard } from "../components/management/MetricCard";
import { ApiError } from "../lib/api";
import { getManagementOverview, type ManagementOverviewResponse } from "../services/management";
import { useI18n } from "../i18n/context";
import type { TranslationKey } from "../i18n/catalog";

export const Route = createFileRoute("/management/")({ component: ManagementOverview });

const surveyCode = "CLIMATE_2026";
function getSurveyStatus(status: string, t: ReturnType<typeof useI18n>["t"]): { label: string; tone: "active" | "neutral" } {
  switch (status) {
    case "DRAFT": return { label: t("management.draft"), tone: "neutral" };
    case "ACTIVE": return { label: t("management.active"), tone: "active" };
    case "CLOSED": return { label: t("management.closed"), tone: "neutral" };
    default: return { label: t("management.statusUnavailable"), tone: "neutral" };
  }
}

function getErrorKey(error: unknown): TranslationKey {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 403: return "management.overviewForbidden";
      case 404: return "management.surveyNotFound";
      case 503: return "management.overviewUnavailable";
      case 0: return "management.connectionError";
    }
  }
  return "management.overviewLoadError";
}

function getNpsValue(data: ManagementOverviewResponse, t: ReturnType<typeof useI18n>["t"], formatPercent: Intl.NumberFormat) {
  if (!data.analytics_available || data.nps === null) return t("management.insufficient");
  return `${data.nps > 0 ? "+" : ""}${formatPercent.format(data.nps)}`;
}

function ManagementOverview() {
  const navigate = useNavigate();
  const [data, setData] = useState<ManagementOverviewResponse | null>(null);
  const [error, setError] = useState<TranslationKey | "">("");
  const [loading, setLoading] = useState(true);
  const { locale, t } = useI18n();
  const numberLocale = locale === "zh" ? "zh-CN" : "pt-BR";
  const formatInteger = new Intl.NumberFormat(numberLocale);
  const formatPercent = new Intl.NumberFormat(numberLocale, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  useEffect(() => {
    let active = true;
    getManagementOverview(surveyCode)
      .then((result) => { if (active) setData(result); })
      .catch((reason: unknown) => {
        if (!active) return;
        if (reason instanceof ApiError && reason.status === 401) {
          void navigate({ to: "/login", replace: true });
          return;
        }
        setError(getErrorKey(reason));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [navigate]);

  const status = data ? getSurveyStatus(data.survey_status, t) : undefined;
  const invitedValue = data?.invited_count === null || !data
    ? t("management.unavailable")
    : formatInteger.format(data.invited_count);
  const invitedDetail = data?.invited_population_source_configured
    ? t("management.invitedConsolidated")
    : t("management.invitedMissing");
  const adherenceValue = data?.adherence_percent === null || !data
    ? t("management.unavailable")
    : `${formatPercent.format(data.adherence_percent)}%`;
  const adherenceDetail = data?.adherence_percent === null || !data
    ? t("management.awaitingInvited")
    : t("management.invitedParticipation");
  const npsDetail = data && (!data.analytics_available || data.nps === null)
    ? t("management.minimum", { count: data.min_group_size })
    : t("management.npsScale");

  return (
    <ManagementLayout>
      <ManagementPageTitle
        eyebrow="management.eyebrow"
        statusBadge={status?.label}
        statusTone={status?.tone}
        title={t("management.surveyTitle")}
        description={t("management.overviewDescription")}
      />
      {loading && (
        <div className="management-pillars-state" role="status" aria-live="polite">
          <span className="management-pillars-state__spinner" aria-hidden="true" />
          <span>{t("management.loadingOverview")}</span>
        </div>
      )}
      {!loading && error && <p className="management-pillars-state management-pillars-state--error" role="alert">{t(error)}</p>}
      {!loading && data && (
        <>
          <section className="management-metrics management-metrics--overview" aria-label={t("management.metricsAria")}>
            <MetricCard label={t("management.index")} value={t("management.underDefinition")} detail={t("management.indexApiUnavailable")} />
            <MetricCard label={t("management.invited")} value={invitedValue} detail={invitedDetail} />
            <MetricCard label={t("management.adherence")} value={adherenceValue} detail={adherenceDetail} />
            <MetricCard label={t("management.completed")} value={formatInteger.format(data.completed_participations)} detail={t("management.completedDetail")} />
            <MetricCard label={t("management.anonymous")} value={formatInteger.format(data.anonymous_response_count)} detail={t("management.anonymousDetail")} />
            <MetricCard label={t("management.nps")} value={getNpsValue(data, t, formatPercent)} detail={npsDetail} />
          </section>
          <p className="management-privacy-note" role="note">
            {t("management.privacy", { count: data.min_group_size })}
          </p>
        </>
      )}
    </ManagementLayout>
  );
}
