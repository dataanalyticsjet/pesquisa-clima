import { mockSurvey } from "../../data/mockSurvey";

type SurveyReviewProps = {
  answers: Record<string, number>;
  onEditPillar: (pillarIndex: number) => void;
};

export function SurveyReview({ answers, onEditPillar }: SurveyReviewProps) {
  const totalQuestions = mockSurvey.pillars.reduce((count, pillar) => count + pillar.questions.length, 0);
  const answeredCount = mockSurvey.pillars.reduce(
    (count, pillar) => count + pillar.questions.filter((question) => answers[question.id] !== undefined).length,
    0,
  );

  return (
    <section className="survey-review" aria-labelledby="survey-review-title">
      <div className="survey-review__heading">
        <div>
          <p className="survey-section-eyebrow">Última etapa</p>
          <h1 id="survey-review-title">Revisar respostas</h1>
          <p>Confira suas respostas antes de concluir a demonstração.</p>
        </div>
        <span className="survey-review__complete">{answeredCount} de {totalQuestions} respondidas</span>
      </div>

      <div className="survey-review__pillars">
        {mockSurvey.pillars.map((pillar, pillarIndex) => {
          const answeredInPillar = pillar.questions.filter((question) => answers[question.id] !== undefined).length;

          return (
            <article className="review-pillar" key={pillar.id}>
              <div className="review-pillar__heading">
                <div>
                  <h2>{pillar.name}</h2>
                  <p>{answeredInPillar} de {pillar.questions.length} respondidas</p>
                </div>
                <button className="review-pillar__edit" onClick={() => onEditPillar(pillarIndex)} type="button">
                  Editar <span className="visually-hidden">respostas de {pillar.name}</span>
                </button>
              </div>
              <ol className="review-pillar__answers">
                {pillar.questions.map((question) => {
                  const responseValue = answers[question.id];
                  const responseLabel = mockSurvey.scale.find((option) => option.value === responseValue)?.label;

                  return (
                    <li key={question.id}>
                      <span>{question.text}</span>
                      <strong>{responseValue}. {responseLabel}</strong>
                    </li>
                  );
                })}
              </ol>
            </article>
          );
        })}
      </div>
    </section>
  );
}
