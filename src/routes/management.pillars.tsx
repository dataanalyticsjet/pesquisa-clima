import { createFileRoute } from "@tanstack/react-router";
import { useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { ManagementPillarApiCard } from "../components/management/ManagementPillarApiCard";
import { ApiError } from "../lib/api";
import { getManagementPillars, type ManagementPillarsResponse } from "../services/management";
import { useI18n } from "../i18n/context";
import type { TranslationKey } from "../i18n/catalog";

export const Route = createFileRoute("/management/pillars")({ component: ManagementPillars });

const surveyCode = "CLIMATE_2026";

function ManagementPillars() {
  const navigate = useNavigate();
  const [data, setData] = useState<ManagementPillarsResponse | null>(null);
  const [error, setError] = useState<TranslationKey | "">("");
  const [loading, setLoading] = useState(true);
  const { t } = useI18n();

  useEffect(() => {
    let active = true;
    getManagementPillars(surveyCode)
      .then((result) => { if (active) setData(result); })
      .catch((reason: unknown) => {
        if (!active) return;
        if (reason instanceof ApiError && reason.status === 401) {
          void navigate({ to: "/login", replace: true });
          return;
        }
        if (reason instanceof ApiError && reason.status === 403) {
          setError("management.pillarsForbidden");
        } else if (reason instanceof ApiError && reason.status === 404) {
          setError("management.surveyNotFound");
        } else if (reason instanceof ApiError && reason.status === 503) {
          setError("management.pillarsUnavailable");
        } else {
          setError("management.resultsLoadError");
        }
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [navigate]);

  return (
    <ManagementLayout>
      <ManagementPageTitle title={t("management.pillarTitle")} description={t("management.pillarDescription")} />
      {loading && (
        <div className="management-pillars-state" role="status" aria-live="polite">
          <span className="management-pillars-state__spinner" aria-hidden="true" />
          <span>{t("management.loadingPillars")}</span>
        </div>
      )}
      {!loading && error && <p className="management-pillars-state management-pillars-state--error" role="alert">{t(error)}</p>}
      {!loading && data && (
        <div className="pillar-score-grid" aria-label={t("management.pillarsAria")}>
          {data.pillars.map((pillar) => (
            <ManagementPillarApiCard
              key={pillar.code}
              pillar={pillar}
              minGroupSize={data.min_group_size}
            />
          ))}
        </div>
      )}
    </ManagementLayout>
  );
}
