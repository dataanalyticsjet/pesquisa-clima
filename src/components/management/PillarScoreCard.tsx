import type { ManagementPillar } from "../../data/mockManagement";
import { DistributionBar } from "./DistributionBar";
import { TrendChart } from "./TrendChart";

export function PillarScoreCard({ pillar, detailed = false }: { pillar: ManagementPillar; detailed?: boolean }) {
  return (
    <article className="pillar-score-card">
      <div className="pillar-score-card__top">
        <div>
          <h2>{pillar.name}</h2>
          <p className="pillar-score-card__trend">Tendência simulada: <strong className={pillar.trend < 0 ? "is-negative" : "is-positive"}>{pillar.trend > 0 ? "+" : ""}{pillar.trend} pts</strong></p>
        </div>
        <div className="pillar-score-card__score" aria-label={"Índice " + pillar.score + " de 100"}><strong>{pillar.score}</strong><span>/ 100</span></div>
      </div>
      <div className="pillar-score-card__meter" role="meter" aria-label={"Índice de " + pillar.name} aria-valuemin={0} aria-valuemax={100} aria-valuenow={pillar.score}><span style={{ width: pillar.score + "%" }} /></div>
      <DistributionBar distribution={pillar.distribution} />

      {detailed && (
        <div className="pillar-score-card__details">
          <h3>Resultados por pergunta oficial</h3>
          <ul className="pillar-question-list">
            {pillar.questions.map((question) => (
              <li key={question.number}><span><small>Q{question.number}</small> {question.text}</span><strong>{question.score}</strong></li>
            ))}
          </ul>
          {pillar.categoricalAnalyses.map((analysis) => (
            <section className="pillar-category-analysis" key={analysis.questionNumber} aria-labelledby={"pillar-category-" + analysis.questionNumber}>
              <h3 id={"pillar-category-" + analysis.questionNumber}>Q{analysis.questionNumber} · {analysis.title}</h3>
              <p>{analysis.text}</p>
              <ul>{analysis.categories.map((category) => (
                <li key={category.label}><span>{category.label}</span><strong>{category.value}%</strong><i aria-hidden="true"><b style={{ width: category.value + "%" }} /></i></li>
              ))}</ul>
            </section>
          ))}
          <TrendChart title={"Evolução simulada de " + pillar.name} values={pillar.evolution} compact />
        </div>
      )}
    </article>
  );
}
