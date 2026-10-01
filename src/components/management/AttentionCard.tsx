import type { ManagementAttention } from "../../data/mockManagement";

const criticalityLabel: Record<ManagementAttention["criticality"], string> = {
  CRITICAL: "Crítico",
  ATTENTION: "Atenção",
  HEALTHY: "Saudável",
};

export function AttentionCard({ item }: { item: ManagementAttention }) {
  return (
    <article className={"attention-card attention-card--" + item.criticality.toLowerCase()}>
      <div className="attention-card__top">
        <div><p className="attention-card__eyebrow">Pilar</p><h2>{item.pillar}</h2></div>
        <span className={"status-badge status-badge--" + item.criticality.toLowerCase()}>{criticalityLabel[item.criticality]}</span>
      </div>
      {item.score !== undefined && <div className="attention-card__score"><strong>{item.score}</strong><span>/ 100</span></div>}
      <dl className="attention-card__context">
        <div><dt>Regional</dt><dd>{item.regional}</dd></div>
        <div><dt>Área</dt><dd>{item.area}</dd></div>
      </dl>
      <p className="attention-card__reason">{item.reason}</p>
      <div className="attention-card__question">
        <span>{item.score === undefined ? "Perguntas categóricas relacionadas" : "Pergunta oficial de maior atenção · Q" + item.questionNumber}</span>
        <p>“{item.question}”</p>
        {item.questionScore !== undefined && <strong>Índice {item.questionScore}</strong>}
      </div>
    </article>
  );
}
