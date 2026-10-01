import { createFileRoute } from "@tanstack/react-router";
import { AttentionCard } from "../components/management/AttentionCard";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { MetricCard } from "../components/management/MetricCard";
import { PillarScoreCard } from "../components/management/PillarScoreCard";
import { TrendChart } from "../components/management/TrendChart";
import { mockManagement } from "../data/mockManagement";

export const Route = createFileRoute("/management/")({ component: ManagementOverview });

const formatInteger = new Intl.NumberFormat("pt-BR");
const formatPercent = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function ManagementOverview() {
  const { survey, pillars, attention, overallEvolution } = mockManagement;
  const orderedPillars = [...pillars].sort((a, b) => b.score - a.score);

  return (
    <ManagementLayout>
      <ManagementPageTitle
        eyebrow="VISÃO DA GESTÃO"
        statusBadge="Pesquisa ativa"
        title={survey.title}
        description="Visão consolidada dos resultados da organização."
      />
      <section className="management-metrics" aria-label="Indicadores gerais">
        <MetricCard label="Índice geral" value={String(survey.overallScore)} detail="de 100 pontos" />
        <MetricCard label="Adesão" value={`${formatPercent.format(survey.adherence)}%`} detail="dos colaboradores convidados" />
        <MetricCard label="Respostas" value={formatInteger.format(survey.responses)} detail="respostas consolidadas" />
        <MetricCard label="Pontos de atenção" value={String(survey.attentionCount)} detail="identificados nesta demonstração" />
      </section>

      <section className="management-section" aria-labelledby="overview-pillars-title">
        <div className="management-section__heading">
          <div>
            <p className="management-eyebrow">RESULTADOS CONSOLIDADOS</p>
            <h2 id="overview-pillars-title">Resultado por pilar</h2>
          </div>
        </div>
        <div className="pillar-score-grid pillar-score-grid--overview">
          {orderedPillars.map((pillar) => <PillarScoreCard key={pillar.id} pillar={pillar} />)}
        </div>
      </section>

      <section className="management-section" aria-labelledby="overview-attention-title">
        <div className="management-section__heading">
          <div>
            <p className="management-eyebrow">PRIORIDADES</p>
            <h2 id="overview-attention-title">Pontos que exigem atenção</h2>
          </div>
        </div>
        <div className="attention-grid">
          {attention.map((item) => <AttentionCard key={item.id} item={item} />)}
        </div>
      </section>

      <section className="management-section management-section--chart" aria-label="Evolução simulada do índice geral">
        <TrendChart title="Evolução simulada do índice geral" values={overallEvolution} />
        <p className="management-demo-note">Série histórica fictícia para demonstração.</p>
      </section>
    </ManagementLayout>
  );
}
