export function SurveyPrivacyNote() {
  return (
    <aside className="survey-privacy-note" aria-labelledby="survey-privacy-title">
      <span className="survey-privacy-note__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24">
          <path d="M12 3.5 19 6v5.3c0 4.4-2.9 7.5-7 9.2-4.1-1.7-7-4.8-7-9.2V6l7-2.5Z" fill="none" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.6" />
          <path d="m9 12 2 2 4-4" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" />
        </svg>
      </span>
      <div>
        <h2 id="survey-privacy-title">Confidencialidade</h2>
        <p>Seu acesso é utilizado apenas para validar sua participação e impedir respostas duplicadas.</p>
        <p>Após o envio, sua identidade não será vinculada ao conteúdo das respostas.</p>
        <p>Os resultados serão analisados de forma consolidada.</p>
      </div>
    </aside>
  );
}
