import { createFileRoute } from "@tanstack/react-router";
import { SurveyCard } from "../components/survey/SurveyCard";
import { SurveyPrivacyNote } from "../components/survey/SurveyPrivacyNote";
import { useSurveyDemo } from "../components/survey/SurveyDemoContext";

export const Route = createFileRoute("/home")({
  component: CollaboratorHome,
});

function CollaboratorHome() {
  const { isCompleted } = useSurveyDemo();

  return (
    <div className="employee-page employee-home">
      <section className="employee-home__intro" aria-labelledby="employee-home-title">
        <p className="survey-section-eyebrow">Área do colaborador</p>
        <h1 id="employee-home-title">Olá, Colaborador</h1>
        <p>Sua opinião ajuda a construir um ambiente de trabalho melhor.</p>
      </section>

      <div className="employee-home__content">
        <SurveyCard completed={isCompleted} />
        <SurveyPrivacyNote />
      </div>
    </div>
  );
}
