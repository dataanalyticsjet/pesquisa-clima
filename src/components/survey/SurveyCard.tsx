import { Link } from "@tanstack/react-router";
import type { SurveyDefinition } from "../../services/surveys";

export function SurveyCard({ completed, survey }: { completed: boolean; survey: SurveyDefinition }) {
  const questionCount = survey.questions.length;
  return (
    <article className={`survey-card${completed ? " survey-card--completed" : ""}`}>
      <div className="survey-card__topline">
        <span className="survey-card__eyebrow">Pesquisa disponível</span>
        <span className={`survey-status${completed ? " survey-status--completed" : ""}`}>
          <span className="survey-status__dot" aria-hidden="true" />
          {completed ? "Concluída" : survey.status === "ACTIVE" ? "Pesquisa ativa" : "Em desenvolvimento"}
        </span>
      </div>

      <h2 className="survey-card__title">{survey.title}</h2>
      {survey.intro_text && <p className="survey-card__description">{survey.intro_text.split(/\n\s*\n/)[0]}</p>}
      {!completed && (
        <div className="survey-card__participation">
          <strong>Participação única</strong>
          <span>Esta pesquisa pode ser respondida uma única vez.</span>
        </div>
      )}

      <dl className="survey-card__details">
        <div>
          <dt>Perguntas</dt>
          <dd>{questionCount}</dd>
        </div>
        <div>
          <dt>Seções</dt>
          <dd>{survey.sections.length}</dd>
        </div>
      </dl>

      {completed ? (
        <p className="survey-card__completed-copy">Obrigado pela sua participação.</p>
      ) : (
        <Link className="survey-button survey-button--primary" to="/survey/clima-2026">
          Responder pesquisa
          <svg aria-hidden="true" viewBox="0 0 24 24">
            <path d="M5 12h14m-6-6 6 6-6 6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
          </svg>
        </Link>
      )}
    </article>
  );
}
