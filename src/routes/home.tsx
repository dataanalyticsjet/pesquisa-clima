import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { SurveyCard } from "../components/survey/SurveyCard";
import { SurveyPrivacyNote } from "../components/survey/SurveyPrivacyNote";
import { ApiError } from "../lib/api";
import { getCurrentUser, type AuthUser } from "../services/auth";
import { getParticipationStatus, getSurveyDefinition, type ParticipationStatus, type SurveyDefinition } from "../services/surveys";
import { canAccessManagement, clearFeishuPostLoginRedirect, hasFeishuPostLoginRedirect } from "../lib/roleNavigation";
import { useI18n } from "../i18n/context";
import type { TranslationKey } from "../i18n/catalog";

export const Route = createFileRoute("/home")({
  component: CollaboratorHome,
});

function CollaboratorHome() {
  const navigate = useNavigate();
  const [data, setData] = useState<{ user: AuthUser; survey: SurveyDefinition; participation: ParticipationStatus } | null>(null);
  const [error, setError] = useState<TranslationKey | "">("");
  const { t } = useI18n();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const shouldRedirectFeishuManagement = hasFeishuPostLoginRedirect();
    getCurrentUser().then(async ({ user }) => {
      if (!active) return;
      if (shouldRedirectFeishuManagement) {
        clearFeishuPostLoginRedirect();
        if (canAccessManagement(user.roles)) {
          void navigate({ to: "/management", replace: true });
          return;
        }
      }
      const [survey, participation] = await Promise.all([getSurveyDefinition("CLIMATE_2026"), getParticipationStatus("CLIMATE_2026")]);
      if (active) setData({ user, survey, participation });
    }).catch((reason: unknown) => {
      if (!active) return;
      if (reason instanceof ApiError && reason.status === 401) void navigate({ to: "/login", replace: true });
      else if (reason instanceof ApiError && reason.status === 404) setError("home.unavailable");
      else if (reason instanceof ApiError && reason.status === 503) setError("home.serviceError");
      else setError("home.loadError");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [navigate]);

  if (loading) return <p role="status" className="api-state">{t("home.loading")}</p>;
  if (error || !data) return <p role="alert" className="api-state">{error ? t(error) : t("home.genericError")}</p>;
  const firstName = data.user.name.trim().split(/\s+/)[0] ?? "Colaborador";
  const displayName = firstName || t("home.defaultName");
  return (
    <div className="employee-page employee-home">
      <section className="employee-home__intro" aria-labelledby="employee-home-title">
        <p className="survey-section-eyebrow">{t("home.area")}</p>
        <h1 id="employee-home-title">{t("home.hello", { name: displayName })}</h1>
        <p>{t("home.intro")}</p>
      </section>

      <div className="employee-home__content">
        <SurveyCard survey={data.survey} completed={data.participation.completed} />
        <SurveyPrivacyNote />
      </div>

    </div>
  );
}
