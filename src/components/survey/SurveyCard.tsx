import { Link } from "@tanstack/react-router";
import type { SurveyDefinition } from "../../services/surveys";
import { useI18n } from "../../i18n/context";
import { localizedSurvey } from "../../i18n/survey.zh";

export function SurveyCard({ completed, survey }: { completed: boolean; survey: SurveyDefinition }) {
  const { locale, t } = useI18n();
  const displaySurvey = localizedSurvey(survey, locale);
  const questionCount = survey.questions.length;
  return (
    <article className={`survey-card${completed ? " survey-card--completed" : ""}`}>
      <div className="survey-card__topline">
          <span className="survey-card__eyebrow">{t("home.available")}</span>
        <span className={`survey-status${completed ? " survey-status--completed" : ""}`}>
          <span className="survey-status__dot" aria-hidden="true" />
          {completed ? t("home.completed") : survey.status === "ACTIVE" ? t("home.active") : t("home.draft")}
        </span>
      </div>

      <h2 className="survey-card__title">{displaySurvey.title}</h2>
      {displaySurvey.intro_text && <p className="survey-card__description">{displaySurvey.intro_text.split(/\n\s*\n/)[0]}</p>}
      {!completed && (
        <div className="survey-card__participation">
          <strong>{t("home.single")}</strong>
          <span>{t("home.singleDescription")}</span>
        </div>
      )}

      <dl className="survey-card__details">
        <div>
          <dt>{t("home.questions")}</dt>
          <dd>{questionCount}</dd>
        </div>
        <div>
          <dt>{t("home.sections")}</dt>
          <dd>{survey.sections.length}</dd>
        </div>
      </dl>

      {completed ? (
        <p className="survey-card__completed-copy">{t("home.thanks")}</p>
      ) : (
        <Link className="survey-button survey-button--primary" to="/survey/clima-2026">
          {t("nav.respond")}
          <svg aria-hidden="true" viewBox="0 0 24 24">
            <path d="M5 12h14m-6-6 6 6-6 6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
          </svg>
        </Link>
      )}
    </article>
  );
}
