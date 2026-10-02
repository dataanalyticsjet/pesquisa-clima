import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { SurveyCard } from "../components/survey/SurveyCard";
import { SurveyPrivacyNote } from "../components/survey/SurveyPrivacyNote";
import { ApiError } from "../lib/api";
import { getCurrentUser, logout, type AuthUser } from "../services/auth";
import { getParticipationStatus, getSurveyDefinition, type ParticipationStatus, type SurveyDefinition } from "../services/surveys";
import { useSurveyDemo } from "../components/survey/SurveyDemoContext";

export const Route = createFileRoute("/home")({
  component: CollaboratorHome,
});

function CollaboratorHome() {
  const navigate = useNavigate();
  const { resetAnswers } = useSurveyDemo();
  const [data, setData] = useState<{ user: AuthUser; survey: SurveyDefinition; participation: ParticipationStatus } | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getCurrentUser().then(async ({ user }) => {
      const [survey, participation] = await Promise.all([getSurveyDefinition("CLIMATE_2026"), getParticipationStatus("CLIMATE_2026")]);
      if (active) setData({ user, survey, participation });
    }).catch((reason: unknown) => {
      if (!active) return;
      if (reason instanceof ApiError && reason.status === 401) void navigate({ to: "/login", replace: true });
      else if (reason instanceof ApiError && reason.status === 404) setError("A pesquisa solicitada não está disponível.");
      else if (reason instanceof ApiError && reason.status === 503) setError("O serviço está temporariamente indisponível. Tente novamente mais tarde.");
      else setError("Não foi possível carregar as informações. Verifique sua conexão e tente novamente.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [navigate]);

  async function handleLogout() {
    try {
      await logout();
      resetAnswers();
      await navigate({ to: "/login", replace: true });
    } catch {
      setError("Não foi possível encerrar sua sessão agora. Tente novamente.");
    }
  }

  if (loading) return <p role="status" className="api-state">Carregando suas informações…</p>;
  if (error || !data) return <p role="alert" className="api-state">{error || "Não foi possível carregar as informações."}</p>;
  const firstName = data.user.name.trim().split(/\s+/)[0] ?? "Colaborador";
  const displayName = firstName ? firstName.charAt(0).toLocaleUpperCase("pt-BR") + firstName.slice(1).toLocaleLowerCase("pt-BR") : "Colaborador";

  return (
    <div className="employee-page employee-home">
      <section className="employee-home__intro" aria-labelledby="employee-home-title">
        <p className="survey-section-eyebrow">Área do colaborador</p>
        <h1 id="employee-home-title">Olá, {displayName}</h1>
        <p>Sua opinião ajuda a construir um ambiente de trabalho melhor.</p>
      </section>

      <div className="employee-home__content">
        <SurveyCard survey={data.survey} completed={data.participation.completed} />
        <SurveyPrivacyNote />
      </div>

      {/* DEMO ONLY
      Remove when real roles are implemented. */}
      <Link className="employee-home__management-link" to="/management">
        Visão Gestão (demo)
      </Link>
      <button className="employee-home__logout" onClick={handleLogout} type="button">Sair</button>
    </div>
  );
}
