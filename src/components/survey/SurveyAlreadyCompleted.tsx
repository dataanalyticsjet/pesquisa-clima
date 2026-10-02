import { Link } from "@tanstack/react-router";

export function SurveyAlreadyCompleted() {
  return (
    <section className="survey-success survey-already-completed" aria-labelledby="survey-already-completed-title">
      <span className="survey-success__icon" aria-hidden="true">
        <svg viewBox="0 0 48 48">
          <circle cx="24" cy="24" r="21" fill="none" stroke="currentColor" strokeWidth="2" />
          <path d="m14 24 7 7 14-15" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" />
        </svg>
      </span>
      <p className="survey-section-eyebrow">Participação concluída</p>
      <h1 id="survey-already-completed-title">Pesquisa já concluída</h1>
      <div className="survey-success__description">
        <p>Você já participou desta pesquisa.</p>
        <p>Para preservar a integridade da pesquisa, é permitido apenas um envio por colaborador.</p>
        <p>Obrigado pela sua participação.</p>
      </div>
      <Link className="survey-button survey-button--primary" to="/home">
        Voltar ao início
      </Link>
    </section>
  );
}
