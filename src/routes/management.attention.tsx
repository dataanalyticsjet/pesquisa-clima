import { createFileRoute } from "@tanstack/react-router";
import { AttentionCard } from "../components/management/AttentionCard";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { useManagementFilters } from "../components/management/ManagementFilters";
import { filterManagementAttention } from "../data/mockManagement";

export const Route = createFileRoute("/management/attention")({ component: ManagementAttention });

function ManagementAttention() {
  const { filters } = useManagementFilters();
  const attention = filterManagementAttention(filters);
  return (
    <ManagementLayout>
      <ManagementPageTitle title="Pontos de atenção identificados" description="Temas que merecem acompanhamento a partir dos resultados consolidados." />
      <p className="management-demo-note">Alertas exibidos por pilar e recorte regional/área demonstrativo. Não há acesso a respostas individuais.</p>
      {attention.length ? <div className="attention-grid attention-grid--page">{attention.map((item) => <AttentionCard key={item.id} item={item} />)}</div> : <p className="management-demo-note">Nenhum alerta mockado corresponde a este recorte.</p>}
      <p className="management-demo-note">Identificação baseada nos resultados consolidados da pesquisa.</p>
    </ManagementLayout>
  );
}
