import { Link } from "@tanstack/react-router";
import { useI18n } from "../../i18n/context";

export function SurveySuccess({ completionText }: { completionText?: string | null }) {
  const { t } = useI18n();
  return (
    <section className="survey-success" aria-labelledby="survey-success-title">
      <span className="survey-success__icon" aria-hidden="true">
        <svg viewBox="0 0 48 48">
          <circle cx="24" cy="24" r="21" fill="none" stroke="currentColor" strokeWidth="2" />
          <path d="m14 24 7 7 14-15" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" />
        </svg>
      </span>
      <p className="survey-section-eyebrow">{t("survey.successEyebrow")}</p>
      <h1 id="survey-success-title">{t("survey.successTitle")}</h1>
      <p className="survey-success__thanks">{completionText || t("survey.successThanks")}</p>
      <div className="survey-success__description">
        <p>{t("survey.successSent")}</p>
        <p>{t("survey.successOnce")}</p>
        <p>{t("survey.successAnonymous")}</p>
      </div>
      <Link className="survey-button survey-button--primary" to="/home">
        {t("survey.backHome")}
      </Link>
    </section>
  );
}
