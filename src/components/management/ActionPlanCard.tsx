import type { ManagementActionPlan } from "../../data/mockManagement";

const statusText: Record<"PLANNED" | "IN_PROGRESS" | "COMPLETED", string> = {
  PLANNED: "Planejado",
  IN_PROGRESS: "Em andamento",
  COMPLETED: "Concluído",
};

export function ActionPlanCard({ plan }: { plan: ManagementActionPlan }) {
  return (
    <article className="action-plan-card">
      <div className="action-plan-card__header">
        <div>
          <p className="management-eyebrow">{plan.pillar}</p>
          <h2>{plan.action}</h2>
        </div>
        <span className={`status-badge status-badge--${plan.status.toLowerCase().replace("_", "-")}`}>
          {statusText[plan.status]}
        </span>
      </div>
      <dl className="action-plan-card__details">
        <div><dt>Escopo</dt><dd>{plan.scope}</dd></div>
        <div><dt>Problema</dt><dd>{plan.problem}</dd></div>
        <div><dt>Responsável</dt><dd>{plan.owner}</dd></div>
        <div><dt>Prazo</dt><dd>{plan.dueDate}</dd></div>
      </dl>
      <div className="action-plan-card__goal">
        <span>Índice atual <strong>{plan.currentScore}</strong></span>
        <span>Meta <strong>{plan.targetScore}</strong></span>
      </div>
      <button className="management-secondary-button" type="button" aria-label={`Acompanhar plano: ${plan.pillar}`}>
        Acompanhar
      </button>
    </article>
  );
}
