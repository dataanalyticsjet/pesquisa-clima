import { createFileRoute } from "@tanstack/react-router";
import { AdherenceList } from "../components/management/AdherenceList";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { MetricCard } from "../components/management/MetricCard";
import { mockManagement } from "../data/mockManagement";

export const Route = createFileRoute("/management/adherence")({ component: ManagementAdherence });

const formatInteger = new Intl.NumberFormat("pt-BR");
const formatPercent = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function ManagementAdherence() {
  const { survey, regionalAdherence } = mockManagement;
  const pending = survey.invited - survey.responses;

  return (
    <ManagementLayout>
      <ManagementPageTitle title="Adesão à pesquisa" description="Acompanhamento agregado da participação por regional." />
      <section className="management-metrics management-metrics--three" aria-label="Resumo da adesão">
        <MetricCard label="Adesão geral" value={`${formatPercent.format(survey.adherence)}%`} />
        <MetricCard label="Convidados" value={formatInteger.format(survey.invited)} />
        <MetricCard label="Responderam" value={formatInteger.format(survey.responses)} />
        <MetricCard label="Pendentes" value={formatInteger.format(pending)} />
      </section>

      <section className="management-section adherence-panel" aria-labelledby="regional-adherence-title">
        <div className="management-section__heading">
          <div>
            <p className="management-eyebrow">PARTICIPAÇÃO AGREGADA</p>
            <h2 id="regional-adherence-title">Adesão por regional</h2>
          </div>
        </div>
        <AdherenceList regions={regionalAdherence} />
      </section>

      <aside className="management-privacy-note">
        <span className="management-privacy-note__icon" aria-hidden="true">i</span>
        <p>O acompanhamento de adesão utiliza somente dados consolidados e não expõe o conteúdo respondido por nenhum colaborador.</p>
      </aside>
      <p className="management-demo-note">Dados fictícios para demonstração.</p>
    </ManagementLayout>
  );
}
