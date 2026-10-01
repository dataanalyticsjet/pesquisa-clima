import { mockSurvey } from "../../data/mockSurvey";

type SurveyIntroProps = {
  onStart: () => void;
};

export function SurveyIntro({ onStart }: SurveyIntroProps) {
  return (
    <section className="survey-intro" aria-labelledby="survey-intro-title">
      <div className="survey-intro__eyebrow">{mockSurvey.introduction[0]}</div>
      <h1 id="survey-intro-title">{mockSurvey.title}</h1>
      <div className="survey-intro__description">
        {mockSurvey.introduction.slice(1).map((paragraph, index) => (
          <p className={index === 3 ? "survey-intro__official-privacy" : undefined} key={paragraph}>{paragraph}</p>
        ))}
      </div>

      <div className="survey-intro__facts" aria-label="Informações da pesquisa">
        <span><strong>{mockSurvey.questions.length}</strong> perguntas</span>
        <span><strong>{mockSurvey.sections.length}</strong> seções</span>
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
