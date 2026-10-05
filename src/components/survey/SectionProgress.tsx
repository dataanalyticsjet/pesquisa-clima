import type { SurveyAnswer } from "../../data/mockSurvey";
import type { SurveyDefinition } from "../../services/surveys";
import { useI18n } from "../../i18n/context";

type SectionProgressProps = { currentSectionIndex: number; answers: Record<string, SurveyAnswer>; survey: SurveyDefinition };

export function SectionProgress({ currentSectionIndex, answers, survey }: SectionProgressProps) {
  const { t } = useI18n();
  const section = survey.sections[currentSectionIndex];
  if (!section) return null;
  const sectionQuestions = survey.questions.filter((question) => question.sectionId === section.id);
  const answeredInSection = sectionQuestions.filter((question) => {
    const answer = answers[question.id];
    return typeof answer === "number" || (typeof answer === "string" && answer.trim().length > 0) || (Array.isArray(answer) && answer.length > 0);
  }).length;
  const progress = Math.round(((currentSectionIndex + 1) / survey.sections.length) * 100);

  return (
    <section className="survey-section-progress" aria-label={t("survey.sectionProgress")}>
      <div className="survey-section-progress__labels">
        <span>{t("survey.sectionNumber", { current: currentSectionIndex + 1, total: survey.sections.length })}</span>
        <span>{t("survey.sectionAnswered", { answered: answeredInSection, total: sectionQuestions.length })}</span>
      </div>
      <strong className="survey-section-progress__name">{section.name}</strong>
      <div className="survey-section-progress__track" aria-hidden="true"><span style={{ width: `${progress}%` }} /></div>
    </section>
  );
}
