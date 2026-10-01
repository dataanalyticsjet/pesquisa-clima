import type { ManagementAttention } from "../../data/mockManagement";

const criticalityLabel: Record<ManagementAttention["criticality"], string> = {
  CRITICAL: "Crítico",
  ATTENTION: "Atenção",
  HEALTHY: "Saudável",
};

export function AttentionCard({ item }: { item: ManagementAttention }) {
  return (
    <article className={`attention-card attention-card--${item.criticality.toLowerCase()}`}>
      <div className="attention-card__top">
        <div>
          <p className="attention-card__eyebrow">Pilar</p>
          <h2>{item.pillar}</h2>
        </div>
        <span className={`status-badge status-badge--${item.criticality.toLowerCase()}`}>
          {criticalityLabel[item.criticality]}
        </span>
      </div>
      <div className="attention-card__score"><strong>{item.score}</strong><span>/ 100</span></div>
      <p className="attention-card__reason">{item.reason}</p>
      <div className="attention-card__question">
        <span>Pergunta de maior atenção</span>
        <p>“{item.question}”</p>
        <strong>Índice {item.questionScore}</strong>
      </div>
    </article>
  );
}
