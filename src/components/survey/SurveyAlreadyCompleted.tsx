import { Link } from "@tanstack/react-router";
import { useI18n } from "../../i18n/context";

export function SurveyAlreadyCompleted() {
  const { t } = useI18n();
  return (
    <section className="survey-success survey-already-completed" aria-labelledby="survey-already-completed-title">
      <span className="survey-success__icon" aria-hidden="true">
        <svg viewBox="0 0 48 48">
          <circle cx="24" cy="24" r="21" fill="none" stroke="currentColor" strokeWidth="2" />
          <path d="m14 24 7 7 14-15" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" />
        </svg>
      </span>
      <p className="survey-section-eyebrow">{t("survey.successEyebrow")}</p>
      <h1 id="survey-already-completed-title">{t("survey.completedTitle")}</h1>
      <div className="survey-success__description">
        <p>{t("survey.completedDescription")}</p>
        <p>{t("survey.completedOnce")}</p>
        <p>{t("survey.completedThanks")}</p>
      </div>
      <Link className="survey-button survey-button--primary" to="/home">
        {t("survey.backHome")}
      </Link>
    </section>
  );
}
