import { createFileRoute } from "@tanstack/react-router";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";

export const Route = createFileRoute("/management/adherence")({ component: ManagementAdherence });

function ManagementAdherence() {
  return (
    <ManagementLayout>
      <ManagementPageTitle title="Adesão à pesquisa" description="Acompanhamento agregado da participação por regional." />
      <div className="management-pillars-state" role="status">
        <span>
          <strong>Dados de adesão ainda indisponíveis</strong><br />
          Fonte oficial de convidados ainda não configurada.
        </span>
      </div>
    </ManagementLayout>
  );
}
