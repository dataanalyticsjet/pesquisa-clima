import type { SurveyAnswer } from "../../data/mockSurvey";
import type { SurveyDefinition } from "../../services/surveys";

type SectionProgressProps = { currentSectionIndex: number; answers: Record<string, SurveyAnswer>; survey: SurveyDefinition };

export function SectionProgress({ currentSectionIndex, answers, survey }: SectionProgressProps) {
  const section = survey.sections[currentSectionIndex];
  if (!section) return null;
  const sectionQuestions = survey.questions.filter((question) => question.sectionId === section.id);
  const answeredInSection = sectionQuestions.filter((question) => {
    const answer = answers[question.id];
    return typeof answer === "number" || (typeof answer === "string" && answer.trim().length > 0) || (Array.isArray(answer) && answer.length > 0);
  }).length;
  const progress = Math.round(((currentSectionIndex + 1) / survey.sections.length) * 100);

  return (
    <section className="survey-section-progress" aria-label="Progresso por seção">
      <div className="survey-section-progress__labels">
        <span>Seção <strong>{currentSectionIndex + 1} de {survey.sections.length}</strong></span>
        <span>{answeredInSection} de {sectionQuestions.length} perguntas respondidas nesta seção</span>
      </div>
      <strong className="survey-section-progress__name">{section.name}</strong>
      <div className="survey-section-progress__track" aria-hidden="true"><span style={{ width: `${progress}%` }} /></div>
    </section>
  );
}
