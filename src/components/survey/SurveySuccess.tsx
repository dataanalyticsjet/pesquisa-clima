import { Link } from "@tanstack/react-router";

// DEMO UI ONLY
// Real single-submission enforcement will be implemented server-side.
export function SurveySuccess() {
  return (
    <section className="survey-success" aria-labelledby="survey-success-title">
      <span className="survey-success__icon" aria-hidden="true">
        <svg viewBox="0 0 48 48">
          <circle cx="24" cy="24" r="21" fill="none" stroke="currentColor" strokeWidth="2" />
          <path d="m14 24 7 7 14-15" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" />
        </svg>
      </span>
      <p className="survey-section-eyebrow">Participação concluída</p>
      <h1 id="survey-success-title">Pesquisa enviada</h1>
      <p className="survey-success__thanks">Obrigada por participar!</p>
      <div className="survey-success__description">
        <p>Seu envio foi concluído.</p>
        <p>Por segurança e integridade da pesquisa, não será possível enviar uma nova resposta.</p>
        <p>Suas respostas permanecem anônimas e serão consideradas apenas nos resultados consolidados.</p>
      </div>
      <Link className="survey-button survey-button--primary" to="/home">
        Voltar ao início
      </Link>
      <p className="survey-success__demo-note">Demonstração: nenhuma resposta foi enviada a um servidor.</p>
    </section>
  );
}
