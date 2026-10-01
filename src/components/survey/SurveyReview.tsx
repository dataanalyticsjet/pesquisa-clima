import { mockSurvey, type SurveyAnswer, type SurveyQuestion } from "../../data/mockSurvey";

type SurveyReviewProps = {
  answers: Record<string, SurveyAnswer>;
  onEditSection: (sectionIndex: number) => void;
};

function answerLabel(question: SurveyQuestion, answer: SurveyAnswer | undefined) {
  if (answer === undefined || answer === "" || (Array.isArray(answer) && answer.length === 0)) return "Não preenchida (opcional)";
  if (typeof answer === "number") {
    if (question.type === "likert") return `${answer} — ${mockSurvey.scale.find((option) => option.value === answer)?.label ?? ""}`;
    if (question.type === "nps") return `${answer} de 10`;
  }
  if (question.type === "textarea" || question.type === "short_text") return "Resposta aberta preenchida";
  const values = Array.isArray(answer) ? answer : [answer];
  return values.map((value) => question.options?.find((option) => option.value === value)?.label ?? value).join(", ");
}

function hasAnswer(value: SurveyAnswer | undefined) {
  return typeof value === "number" || (typeof value === "string" && value.trim().length > 0) || (Array.isArray(value) && value.length > 0);
}

export function SurveyReview({ answers, onEditSection }: SurveyReviewProps) {
  const totalQuestions = mockSurvey.questions.length;
  const answeredCount = mockSurvey.questions.filter((question) => hasAnswer(answers[question.id])).length;

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

      <div className="survey-review__sections">
        {mockSurvey.sections.map((section, sectionIndex) => {
          const sectionQuestions = mockSurvey.questions.filter((question) => question.sectionId === section.id);
          const answeredInSection = sectionQuestions.filter((question) => hasAnswer(answers[question.id])).length;

          return (
            <article className="review-section" key={section.id}>
              <div className="review-section__header">
                <details className="review-section__details">
                  <summary className="review-section__summary">
                    <span className="review-section__name">{section.name}</span>
                    <span className="review-section__count">{answeredInSection} de {sectionQuestions.length} respondidas</span>
                  </summary>
                  <div className="review-section__content">
                    <ol className="review-section__answers">
                      {sectionQuestions.map((question) => (
                        <li key={question.id}>
                          <span>{question.number}. {question.text}</span>
                          <strong>{answerLabel(question, answers[question.id])}</strong>
                        </li>
                      ))}
                    </ol>
                  </div>
                </details>
                <button className="review-section__edit" onClick={() => onEditSection(sectionIndex)} type="button">
                  Editar
                  <span className="visually-hidden"> seção {section.name}</span>
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
