import type { SurveyAnswer, SurveyQuestion } from "../../data/mockSurvey";
import type { SurveyDefinition } from "../../services/surveys";
import { useI18n } from "../../i18n/context";

type SurveyReviewProps = {
  answers: Record<string, SurveyAnswer>;
  onEditSection: (sectionIndex: number) => void;
  survey: SurveyDefinition;
};

function answerLabel(question: SurveyQuestion, answer: SurveyAnswer | undefined, t: ReturnType<typeof useI18n>["t"]) {
  if (answer === undefined || answer === "" || (Array.isArray(answer) && answer.length === 0)) return t("survey.notAnswered");
  if (typeof answer === "number") return `${answer}`;
  if (question.type === "textarea" || question.type === "short_text") return t("survey.openFilled");
  const values = Array.isArray(answer) ? answer : [answer];
  return values.map((value) => {
    const option = question.options?.find((item) => item.value === value);
    if (!option) return value;
    if (question.type === "likert" && option.score !== undefined) return `${option.score} — ${option.label}`;
    if (question.type === "nps" && option.score !== undefined) return t("survey.outOfTen", { score: option.score });
    return option.label;
  }).join(", ");
}

function hasAnswer(value: SurveyAnswer | undefined) {
  return typeof value === "number" || (typeof value === "string" && value.trim().length > 0) || (Array.isArray(value) && value.length > 0);
}

export function SurveyReview({ answers, onEditSection, survey }: SurveyReviewProps) {
  const { t } = useI18n();
  const totalQuestions = survey.questions.length;
  const answeredCount = survey.questions.filter((question) => hasAnswer(answers[question.id])).length;

  return (
    <section className="survey-review" aria-labelledby="survey-review-title">
      <div className="survey-review__heading">
        <div>
          <p className="survey-section-eyebrow">{t("survey.lastStep")}</p>
          <h1 id="survey-review-title">{t("survey.reviewTitle")}</h1>
          <p>{t("survey.reviewDescription")}</p>
        </div>
        <span className="survey-review__complete">{t("survey.answerCount", { answered: answeredCount, total: totalQuestions })}</span>
      </div>

      <div className="survey-review__sections">
        {survey.sections.map((section, sectionIndex) => {
          const sectionQuestions = survey.questions.filter((question) => question.sectionId === section.id);
          const answeredInSection = sectionQuestions.filter((question) => hasAnswer(answers[question.id])).length;

          return (
            <article className="review-section" key={section.id}>
              <div className="review-section__header">
                <details className="review-section__details">
                  <summary className="review-section__summary">
                    <span className="review-section__name">{section.name}</span>
                    <span className="review-section__count">{t("survey.answerCount", { answered: answeredInSection, total: sectionQuestions.length })}</span>
                  </summary>
                  <div className="review-section__content">
                    <ol className="review-section__answers">
                      {sectionQuestions.map((question) => (
                        <li key={question.id}>
                          <span>{question.number}. {question.text}</span>
                          <strong>{answerLabel(question, answers[question.id], t)}</strong>
                        </li>
                      ))}
                    </ol>
                  </div>
                </details>
                <button className="review-section__edit" onClick={() => onEditSection(sectionIndex)} type="button">
                  {t("survey.edit")}
                  <span className="visually-hidden">{t("survey.sectionAccessible", { name: section.name })}</span>
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
