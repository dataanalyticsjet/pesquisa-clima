import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { MetricCard } from "../components/management/MetricCard";
import { ApiError } from "../lib/api";
import { getManagementOverview, type ManagementOverviewResponse } from "../services/management";

export const Route = createFileRoute("/management/")({ component: ManagementOverview });

const surveyCode = "CLIMATE_2026";
const formatInteger = new Intl.NumberFormat("pt-BR");
const formatPercent = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function getSurveyStatus(status: string): { label: string; tone: "active" | "neutral" } {
  switch (status) {
    case "DRAFT": return { label: "Rascunho", tone: "neutral" };
    case "ACTIVE": return { label: "Ativa", tone: "active" };
    case "CLOSED": return { label: "Encerrada", tone: "neutral" };
    default: return { label: "Status indisponível", tone: "neutral" };
  }
}

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 403: return "Seu perfil não tem autorização para acessar a visão da gestão.";
      case 404: return "A pesquisa solicitada não foi encontrada.";
      case 503: return "A visão da gestão está temporariamente indisponível. Tente novamente mais tarde.";
      case 0: return "Não foi possível conectar ao serviço. Verifique sua conexão e tente novamente.";
    }
  }
  return "Não foi possível carregar a visão da gestão. Tente novamente mais tarde.";
}

function getNpsValue(data: ManagementOverviewResponse) {
  if (!data.analytics_available || data.nps === null) return "Dados insuficientes";
  return `${data.nps > 0 ? "+" : ""}${formatPercent.format(data.nps)}`;
}

function ManagementOverview() {
  const navigate = useNavigate();
  const [data, setData] = useState<ManagementOverviewResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

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
        setError(getErrorMessage(reason));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [navigate]);

  const status = data ? getSurveyStatus(data.survey_status) : undefined;
  const invitedValue = data?.invited_count === null || !data
    ? "Indisponível"
    : formatInteger.format(data.invited_count);
  const invitedDetail = data?.invited_population_source_configured
    ? "População convidada consolidada"
    : "Fonte de convidados ainda não configurada";
  const adherenceValue = data?.adherence_percent === null || !data
    ? "Indisponível"
    : `${formatPercent.format(data.adherence_percent)}%`;
  const adherenceDetail = data?.adherence_percent === null || !data
    ? "Aguardando fonte oficial de convidados"
    : "Participação sobre a população convidada";
  const npsDetail = data && (!data.analytics_available || data.nps === null)
    ? `Mínimo de ${data.min_group_size} respostas necessário`
    : "Escala de -100 a +100";

  return (
    <ManagementLayout>
      <ManagementPageTitle
        eyebrow="VISÃO DA GESTÃO"
        statusBadge={status?.label}
        statusTone={status?.tone}
        title="Pesquisa de Clima 2026"
        description="Visão consolidada dos resultados da organização."
      />
      {loading && (
        <div className="management-pillars-state" role="status" aria-live="polite">
          <span className="management-pillars-state__spinner" aria-hidden="true" />
          <span>Carregando dados consolidados…</span>
        </div>
      )}
      {!loading && error && <p className="management-pillars-state management-pillars-state--error" role="alert">{error}</p>}
      {!loading && data && (
        <>
          <section className="management-metrics management-metrics--overview" aria-label="Indicadores consolidados da pesquisa">
            <MetricCard label="Índice geral" value="Em definição" detail="Indicador ainda não disponível na API." />
            <MetricCard label="Convidados" value={invitedValue} detail={invitedDetail} />
            <MetricCard label="Adesão" value={adherenceValue} detail={adherenceDetail} />
            <MetricCard label="Participações concluídas" value={formatInteger.format(data.completed_participations)} detail="Participações registradas na pesquisa." />
            <MetricCard label="Respostas anônimas" value={formatInteger.format(data.anonymous_response_count)} detail="Contagem agregada de respostas recebidas." />
            <MetricCard label="NPS" value={getNpsValue(data)} detail={npsDetail} />
          </section>
          <p className="management-privacy-note" role="note">
            Os indicadores são apresentados de forma consolidada. Resultados sujeitos ao mínimo de {data.min_group_size} respostas para preservar a confidencialidade.
          </p>
        </>
      )}
    </ManagementLayout>
  );
}
