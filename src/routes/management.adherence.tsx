import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AdherenceList } from "../components/management/AdherenceList";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { MetricCard } from "../components/management/MetricCard";
import { ApiError } from "../lib/api";
import { useI18n } from "../i18n/context";
import { downloadManagementAdherence, getManagementAdherence, type ManagementAdherenceResponse } from "../services/management";
import type { TranslationKey } from "../i18n/catalog";

export const Route = createFileRoute("/management/adherence")({ component: ManagementAdherence });

const surveyCode = "CLIMATE_2026";

function getErrorKey(error: unknown): TranslationKey {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 403: return "management.adherenceForbidden";
      case 404: return "management.surveyNotFound";
      case 503: return "management.adherenceUnavailable";
      case 0: return "management.connectionError";
    }
  }
  return "management.adherenceLoadError";
}

function ManagementAdherence() {
  const navigate = useNavigate();
  const { locale, t } = useI18n();
  const [data, setData] = useState<ManagementAdherenceResponse | null>(null);
  const [error, setError] = useState<TranslationKey | "">("");
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<TranslationKey | "">("");
  const [exportComplete, setExportComplete] = useState(false);
  const formatInteger = new Intl.NumberFormat(locale === "zh" ? "zh-CN" : "pt-BR");

  async function handleExport() {
    setExportError("");
    setExportComplete(false);
    setExporting(true);
    try {
      const { blob, filename } = await downloadManagementAdherence(surveyCode, locale);
      const objectUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = filename;
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 1_000);
      setExportComplete(true);
    } catch (reason: unknown) {
      if (reason instanceof ApiError && reason.status === 401) {
        void navigate({ to: "/login", replace: true });
        return;
      }
      if (reason instanceof ApiError) {
        if (reason.status === 403) setExportError("management.adherenceForbidden");
        else if (reason.status === 404) setExportError("management.surveyNotFound");
        else if (reason.status === 0) setExportError("management.connectionError");
        else setExportError("management.adherenceExportError");
      } else {
        setExportError("management.adherenceExportError");
      }
    } finally {
      setExporting(false);
    }
  }

  useEffect(() => {
    let active = true;
    getManagementAdherence(surveyCode)
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

  return (
    <ManagementLayout>
      <ManagementPageTitle title={t("management.adherenceTitle")} description={t("management.adherenceDescription")} />
      {!loading && data && (
        <div className="adherence-toolbar">
          <button className="adherence-export" type="button" onClick={() => void handleExport()} disabled={exporting}>
            {exporting ? t("management.adherenceExporting") : t("management.adherenceExport")}
          </button>
          {exportError && <p className="adherence-export__message adherence-export__message--error" role="alert">{t(exportError)}</p>}
          {exportComplete && <p className="adherence-export__message" role="status">{t("management.adherenceExportComplete")}</p>}
        </div>
      )}
      {loading && (
        <div className="management-pillars-state" role="status" aria-live="polite">
          <span className="management-pillars-state__spinner" aria-hidden="true" />
          <span>{t("management.adherenceLoading")}</span>
        </div>
      )}
      {!loading && error && (
        <p className="management-pillars-state management-pillars-state--error" role="alert">{t(error)}</p>
      )}
      {!loading && data && (
        <>
          <section className="management-metrics" aria-label={t("management.adherenceMetricsAria")}>
            <MetricCard
              label={t("management.formsCompleted")}
              value={formatInteger.format(data.total_responses)}
              detail={t("management.adherenceTotalDetail")}
            />
            <MetricCard
              label={t("management.totalRegionals")}
              value={formatInteger.format(data.total_regionals)}
            />
            <MetricCard
              label={t("management.totalBases")}
              value={formatInteger.format(data.total_bases)}
            />
            <MetricCard
              label={t("management.regionalsWithResults")}
              value={formatInteger.format(data.regionals_with_results)}
              detail={t("management.regionalsWithResultsDetail", { count: data.min_group_size })}
            />
          </section>
          <p className="management-privacy-note" role="note">
            <span className="management-privacy-note__icon" aria-hidden="true">i</span>
            <span>{t("management.adherencePrivacy", { count: data.min_group_size })}</span>
          </p>
          {data.total_responses === 0 && (
            <p className="management-pillars-state" role="status">{t("management.adherenceEmpty")}</p>
          )}
          {data.regionals.length === 0 ? (
            <p className="management-pillars-state" role="status">{t("management.adherenceEmptyGroups")}</p>
          ) : (
            <section className="adherence-panel" aria-label={t("management.adherenceRegionalsAria")}>
              <AdherenceList regionals={data.regionals} />
            </section>
          )}
        </>
      )}
    </ManagementLayout>
  );
}
