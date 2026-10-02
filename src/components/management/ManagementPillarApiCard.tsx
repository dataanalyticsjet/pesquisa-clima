import type { ManagementPillar } from "../../services/management";

const formatIndex = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });

export function ManagementPillarApiCard({
  pillar,
  minGroupSize,
}: {
  pillar: ManagementPillar;
  minGroupSize: number;
}) {
  const index = pillar.analytics_available ? pillar.index : null;
  const hasIndex = index !== null;
  const unavailableTitle = pillar.respondent_count === 0 ? "Sem respostas" : "Dados insuficientes";
  const unavailableDescription = pillar.respondent_count === 0
    ? "Aguardando respostas para compor o índice."
    : !pillar.analytics_available
      ? `Mínimo de ${minGroupSize} respostas necessário.`
      : "O índice não está disponível neste momento.";

  return (
    <article className="pillar-score-card management-pillar-api-card">
      <div className="pillar-score-card__top">
        <div className="management-pillar-api-card__heading">
          <h2>{pillar.title}</h2>
          <p className="management-pillar-api-card__questions">
            {pillar.question_count} {pillar.question_count === 1 ? "pergunta considerada" : "perguntas consideradas"}
          </p>
        </div>
        {hasIndex ? (
          <div
            className="pillar-score-card__score"
            aria-label={`Índice ${formatIndex.format(index)} de 100`}
          >
            <strong>{formatIndex.format(index)}</strong>
            <span>/ 100</span>
          </div>
        ) : null}
      </div>

      {hasIndex ? (
        <div
          className="pillar-score-card__meter"
          role="meter"
          aria-label={`Índice de ${pillar.title}`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={index}
        >
          <span style={{ width: `${index}%` }} />
        </div>
      ) : (
        <div className="management-pillar-api-card__unavailable" role="status">
          <strong>{unavailableTitle}</strong>
          <span>{unavailableDescription}</span>
        </div>
      )}
    </article>
  );
}
