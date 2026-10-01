import { createFileRoute } from "@tanstack/react-router";
import { ActionPlanCard } from "../components/management/ActionPlanCard";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { mockManagement } from "../data/mockManagement";

export const Route = createFileRoute("/management/action-plans")({ component: ManagementActionPlans });

function ManagementActionPlans() {
  return (
    <ManagementLayout>
      <ManagementPageTitle title="Planos de ação" description="Ações simuladas para acompanhar os temas priorizados nos resultados." />
      <div className="action-plan-grid">
        {mockManagement.actionPlans.map((plan) => <ActionPlanCard key={plan.id} plan={plan} />)}
      </div>
      <p className="management-demo-note">Planos demonstrativos. Edição e acompanhamento real ainda não estão disponíveis.</p>
    </ManagementLayout>
  );
}
