import type { SurveyDefinition } from "../../services/surveys";
import { useI18n } from "../../i18n/context";

type SurveyIntroProps = {
  onStart: () => void;
  survey: SurveyDefinition;
};

export function SurveyIntro({ onStart, survey }: SurveyIntroProps) {
  const { t } = useI18n();
  const paragraphs = (survey.intro_text ?? "").split(/\n\s*\n/).filter((paragraph) => paragraph.length > 0);
  return (
    <section className="survey-intro" aria-labelledby="survey-intro-title">
      <div className="survey-intro__eyebrow">{paragraphs[0] ?? ""}</div>
      <h1 id="survey-intro-title">{survey.title}</h1>
      <div className="survey-intro__description">
        {paragraphs.slice(1).map((paragraph, index) => (
          <p className={index === 3 ? "survey-intro__official-privacy" : undefined} key={`${index}-${paragraph.slice(0, 24)}`}>{paragraph}</p>
        ))}
      </div>

      <aside className="survey-intro__participation" aria-labelledby="survey-intro-participation-title">
        <span className="survey-intro__participation-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path d="M12 3.5 19 6v5.3c0 4.4-2.9 7.5-7 9.2-4.1-1.7-7-4.8-7-9.2V6l7-2.5Z" fill="none" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.6" />
            <path d="m9 12 2 2 4-4" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" />
          </svg>
        </span>
        <div>
          <h2 id="survey-intro-participation-title">{t("survey.protection")}</h2>
          <ul>
            <li>{t("survey.protectOnce")}</li>
            <li>{t("survey.protectAccess")}</li>
            <li>{t("survey.protectIdentity")}</li>
            <li>{t("survey.protectResults")}</li>
          </ul>
        </div>
      </aside>

      <div className="survey-intro__facts" aria-label={t("survey.info")}>
        <span><strong>{survey.questions.length}</strong> {t("survey.questions")}</span>
        <span><strong>{survey.sections.length}</strong> {t("survey.sections")}</span>
      </div>

      <button className="survey-button survey-button--primary" onClick={onStart} type="button">
        {t("survey.start")}
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M5 12h14m-6-6 6 6-6 6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
        </svg>
      </button>
    </section>
  );
}
