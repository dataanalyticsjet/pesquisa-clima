import { createFileRoute } from "@tanstack/react-router";
import { ActionPlanCard } from "../components/management/ActionPlanCard";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { useManagementFilters } from "../components/management/ManagementFilters";
import { mockManagement } from "../data/mockManagement";

export const Route = createFileRoute("/management/action-plans")({ component: ManagementActionPlans });

function ManagementActionPlans() {
  const { filters } = useManagementFilters();
  const plans = mockManagement.actionPlans.filter((plan) =>
    plan.scope === "Corporativo"
    || ((!filters.regional || plan.regional === filters.regional)
      && (!filters.area || plan.area === filters.area)
      && (!filters.base || plan.base === filters.base)
      && (!filters.cnpj || plan.cnpj === filters.cnpj)),
  );
  return (
    <ManagementLayout>
      <ManagementPageTitle title="Planos de ação" description="Ações simuladas para acompanhar os temas priorizados nos resultados." />
      {plans.length ? <div className="action-plan-grid">{plans.map((plan) => <ActionPlanCard key={plan.id} plan={plan} />)}</div> : <p className="management-demo-note">Nenhum plano mockado corresponde a este recorte.</p>}
      <p className="management-demo-note">Planos demonstrativos. Edição e acompanhamento real ainda não estão disponíveis.</p>
    </ManagementLayout>
  );
}
