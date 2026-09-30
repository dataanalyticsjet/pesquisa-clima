import { mockSurvey } from "../../data/mockSurvey";

type SurveyIntroProps = {
  onStart: () => void;
};

const assurances = [
  "Não existem respostas certas ou erradas.",
  "Responda considerando a sua experiência.",
  "As respostas serão analisadas de forma agrupada.",
  "Sua identidade não será vinculada ao conteúdo respondido.",
];

export function SurveyIntro({ onStart }: SurveyIntroProps) {
  const questionCount = mockSurvey.pillars.reduce((count, pillar) => count + pillar.questions.length, 0);

  return (
    <section className="survey-intro" aria-labelledby="survey-intro-title">
      <div className="survey-intro__eyebrow">Sua participação faz a diferença</div>
      <h1 id="survey-intro-title">{mockSurvey.title}</h1>
      <p className="survey-intro__description">{mockSurvey.description}</p>

      <div className="survey-intro__facts" aria-label="Informações da pesquisa">
        <span><strong>{questionCount}</strong> perguntas</span>
        <span><strong>{mockSurvey.pillars.length}</strong> pilares</span>
        <span>aproximadamente <strong>{mockSurvey.estimatedTimeMinutes} minutos</strong></span>
      </div>

      <div className="survey-intro__privacy">
        <h2>Sua participação é confidencial</h2>
        <ul>
          {assurances.map((assurance) => (
            <li key={assurance}>
              <span aria-hidden="true">✓</span>
              {assurance}
            </li>
          ))}
        </ul>
      </div>

      <button className="survey-button survey-button--primary" onClick={onStart} type="button">
        Começar pesquisa
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M5 12h14m-6-6 6 6-6 6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
        </svg>
      </button>
    </section>
  );
}
