import { createFileRoute } from "@tanstack/react-router";
import { AttentionCard } from "../components/management/AttentionCard";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { mockManagement } from "../data/mockManagement";

export const Route = createFileRoute("/management/attention")({ component: ManagementAttention });

function ManagementAttention() {
  return (
    <ManagementLayout>
      <ManagementPageTitle title="Pontos de atenção identificados" description="Temas que merecem acompanhamento a partir dos resultados consolidados." />
      <div className="attention-grid attention-grid--page">
        {mockManagement.attention.map((item) => <AttentionCard key={item.id} item={item} />)}
      </div>
      <p className="management-demo-note">Identificação baseada nos resultados consolidados da pesquisa.</p>
    </ManagementLayout>
  );
}
