import { mockSurvey, type SurveyAnswer } from "../../data/mockSurvey";

type SectionProgressProps = { currentSectionIndex: number; answers: Record<string, SurveyAnswer> };

export function SectionProgress({ currentSectionIndex, answers }: SectionProgressProps) {
  const section = mockSurvey.sections[currentSectionIndex];
  const sectionQuestions = mockSurvey.questions.filter((question) => question.sectionId === section.id);
  const answeredInSection = sectionQuestions.filter((question) => {
    const answer = answers[question.id];
    return typeof answer === "number" || (typeof answer === "string" && answer.trim().length > 0) || (Array.isArray(answer) && answer.length > 0);
  }).length;
  const progress = Math.round(((currentSectionIndex + 1) / mockSurvey.sections.length) * 100);

  return (
    <section className="survey-section-progress" aria-label="Progresso por seção">
      <div className="survey-section-progress__labels">
        <span>Seção <strong>{currentSectionIndex + 1} de {mockSurvey.sections.length}</strong></span>
        <span>{answeredInSection} de {sectionQuestions.length} perguntas respondidas nesta seção</span>
      </div>
      <strong className="survey-section-progress__name">{section.name}</strong>
      <div className="survey-section-progress__track" aria-hidden="true"><span style={{ width: `${progress}%` }} /></div>
    </section>
  );
}
