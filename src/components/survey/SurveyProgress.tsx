type SurveyProgressProps = {
  answeredCount: number;
  totalCount: number;
};

export function SurveyProgress({ answeredCount, totalCount }: SurveyProgressProps) {
  const percentage = totalCount === 0 ? 0 : Math.round((answeredCount / totalCount) * 100);

  return (
    <section className="survey-progress" aria-label="Progresso da pesquisa">
      <div className="survey-progress__labels">
        <span>{answeredCount} de {totalCount} respondidas</span>
        <strong>{percentage}%</strong>
      </div>
      <div
        className="survey-progress__track"
        role="progressbar"
        aria-label="Perguntas respondidas"
        aria-valuemin={0}
        aria-valuemax={totalCount}
        aria-valuenow={answeredCount}
        aria-valuetext={`${percentage}% concluído`}
      >
        <span className="survey-progress__value" style={{ width: `${percentage}%` }} />
      </div>
    </section>
  );
}
