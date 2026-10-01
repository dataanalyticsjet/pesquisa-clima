import type { ManagementPillar } from "../../data/mockManagement";
import { DistributionBar } from "./DistributionBar";
import { TrendChart } from "./TrendChart";

export function PillarScoreCard({ pillar, detailed = false }: { pillar: ManagementPillar; detailed?: boolean }) {
  return (
    <article className="pillar-score-card">
      <div className="pillar-score-card__top">
        <div>
          <h2>{pillar.name}</h2>
          <p className="pillar-score-card__trend">
            Tendência simulada: <strong className={pillar.trend < 0 ? "is-negative" : "is-positive"}>
              {pillar.trend > 0 ? "+" : ""}{pillar.trend} pts
            </strong>
          </p>
        </div>
        <div className="pillar-score-card__score" aria-label={`Índice ${pillar.score} de 100`}>
          <strong>{pillar.score}</strong><span>/ 100</span>
        </div>
      </div>
      <div className="pillar-score-card__meter" role="meter" aria-label={`Índice de ${pillar.name}`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={pillar.score}>
        <span style={{ width: `${pillar.score}%` }} />
      </div>
      <DistributionBar distribution={pillar.distribution} />

      {detailed && (
        <div className="pillar-score-card__details">
          <h3>Resultado por pergunta</h3>
          <ul className="pillar-question-list">
            {pillar.questions.map((question) => (
              <li key={question.text}>
                <span>{question.text}</span>
                <strong>{question.score}</strong>
              </li>
            ))}
          </ul>
          <TrendChart title={`Evolução de ${pillar.name}`} values={pillar.evolution} compact />
        </div>
      )}
    </article>
  );
}
