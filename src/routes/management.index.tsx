import { createFileRoute } from "@tanstack/react-router";
import { AttentionCard } from "../components/management/AttentionCard";
import { ManagementNpsSummary, ManagementOverviewAnalysis } from "../components/management/ManagementAnalysis";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { MetricCard } from "../components/management/MetricCard";
import { PillarScoreCard } from "../components/management/PillarScoreCard";
import { TrendChart } from "../components/management/TrendChart";
import { useManagementFilters } from "../components/management/ManagementFilters";
import { averageScore, filterManagementAttention, filterManagementSegments, mockManagement } from "../data/mockManagement";

export const Route = createFileRoute("/management/")({ component: ManagementOverview });

const formatInteger = new Intl.NumberFormat("pt-BR");
const formatPercent = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function ManagementOverview() {
  const { filters } = useManagementFilters();
  const { survey, pillars, overallEvolution } = mockManagement;
  const hasFilters = Object.values(filters).some(Boolean);
  const matched = filterManagementSegments(filters);
  const segments = matched.filter((segment) => !segment.protected);
  const privateOnly = matched.length > 0 && segments.length === 0;
  const attention = filterManagementAttention(filters);
  const scopedScores = segments.flatMap((segment) => pillars.map((pillar) => segment.pillarScores[pillar.id]))
    .filter((score): score is number => typeof score === "number");
  const overallScore = hasFilters ? averageScore(scopedScores) : survey.overallScore;
  const responseCount = hasFilters ? segments.reduce((sum, segment) => sum + segment.responseCount, 0) : survey.responses;
  const orderedPillars = pillars.map((pillar) => {
    const score = hasFilters
      ? averageScore(segments.map((segment) => segment.pillarScores[pillar.id]).filter((value): value is number => typeof value === "number"))
      : pillar.score;
    const safeScore = score ?? pillar.score;
    const neutral = 18;
    const negative = Math.max(8, Math.min(60, 100 - safeScore));
    return { ...pillar, score: safeScore, distribution: hasFilters ? { positive: 100 - neutral - negative, neutral, negative } : pillar.distribution };
  }).sort((a, b) => b.score - a.score);

  return (
    <ManagementLayout>
      <ManagementPageTitle eyebrow="VISÃO DA GESTÃO" statusBadge="Pesquisa ativa" title={survey.title} description="Visão consolidada dos resultados da organização." />
      {privateOnly && <div className="management-protected-state" role="status"><strong>Dados indisponíveis para preservar a confidencialidade.</strong><span>Resultados exibidos somente de forma consolidada. Nenhuma resposta individual é disponibilizada.</span></div>}
      {!privateOnly && <>
        <section className="management-metrics" aria-label="Indicadores do recorte selecionado">
          <MetricCard label="Índice geral" value={overallScore === null ? "—" : String(overallScore)} detail={hasFilters ? "média mockada do recorte" : "de 100 pontos"} />
          <MetricCard label="Adesão" value={formatPercent.format(survey.adherence) + "%"} detail="indicador geral demonstrativo" />
          <MetricCard label="Respostas" value={formatInteger.format(responseCount)} detail={hasFilters ? "contagem consolidada fictícia" : "respostas consolidadas"} />
          <MetricCard label="Pontos de atenção" value={String(attention.length)} detail="no recorte selecionado" />
        </section>
        <section className="management-section" aria-labelledby="overview-pillars-title">
          <div className="management-section__heading"><div><p className="management-eyebrow">RESULTADOS CONSOLIDADOS</p><h2 id="overview-pillars-title">Resultado por pilar</h2></div></div>
          <div className="pillar-score-grid pillar-score-grid--overview">{orderedPillars.map((pillar) => <PillarScoreCard key={pillar.id} pillar={pillar} />)}</div>
        </section>
      </>}
      {!privateOnly && <ManagementNpsSummary />}
      <ManagementOverviewAnalysis />
      <section className="management-section" aria-labelledby="overview-attention-title">
        <div className="management-section__heading"><div><p className="management-eyebrow">PRIORIDADES</p><h2 id="overview-attention-title">Pontos que exigem atenção</h2></div></div>
        {attention.length ? <div className="attention-grid">{attention.map((item) => <AttentionCard key={item.id} item={item} />)}</div> : <p className="management-demo-note">Nenhum alerta mockado corresponde a este recorte.</p>}
      </section>
      {!hasFilters && <section className="management-section management-section--chart" aria-label="Evolução simulada do índice geral"><TrendChart title="Evolução simulada do índice geral" values={overallEvolution} /><p className="management-demo-note">Série histórica fictícia para demonstração.</p></section>}
    </ManagementLayout>
  );
}
