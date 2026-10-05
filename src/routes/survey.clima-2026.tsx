import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { SurveyFlow } from "../components/survey/SurveyFlow";
import { SurveyAlreadyCompleted } from "../components/survey/SurveyAlreadyCompleted";
import { ApiError } from "../lib/api";
import { getCurrentUser } from "../services/auth";
import { getParticipationStatus, getSurveyDefinition, type ParticipationStatus, type SurveyDefinition } from "../services/surveys";
import { useNavigate } from "@tanstack/react-router";
import { useI18n } from "../i18n/context";
import type { TranslationKey } from "../i18n/catalog";

export const Route = createFileRoute("/survey/clima-2026")({
  component: SurveyPage,
});

function SurveyPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<{ survey: SurveyDefinition; participation: ParticipationStatus } | null>(null);
  const [error, setError] = useState<TranslationKey | "">("");
  const [loading, setLoading] = useState(true);
  const { t } = useI18n();

  useEffect(() => {
    let active = true;
    getCurrentUser().then(async () => {
      const [survey, participation] = await Promise.all([getSurveyDefinition("CLIMATE_2026"), getParticipationStatus("CLIMATE_2026")]);
      if (active) setData({ survey, participation });
    }).catch((reason: unknown) => {
      if (!active) return;
      if (reason instanceof ApiError && reason.status === 401) void navigate({ to: "/login", replace: true });
      else if (reason instanceof ApiError && reason.status === 404) setError("home.unavailable");
      else if (reason instanceof ApiError && reason.status === 503) setError("survey.serviceError");
      else setError("survey.loadError");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [navigate]);

  if (loading) return <p role="status" className="api-state">{t("survey.loading")}</p>;
  if (error || !data) return <p role="alert" className="api-state">{error ? t(error) : t("survey.genericError")}</p>;
  if (data.participation.completed) return <SurveyAlreadyCompleted />;
  return <SurveyFlow survey={data.survey} />;
}
