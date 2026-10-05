type SurveyProgressProps = {
  answeredCount: number;
  totalCount: number;
};

export function SurveyProgress({ answeredCount, totalCount }: SurveyProgressProps) {
  const percentage = totalCount === 0 ? 0 : Math.round((answeredCount / totalCount) * 100);
  const { t } = useI18n();

  return (
    <section className="survey-progress" aria-label={t("survey.progress")}>
      <div className="survey-progress__labels">
        <span>{t("survey.answerCount", { answered: answeredCount, total: totalCount })}</span>
        <strong>{percentage}%</strong>
      </div>
      <div
        className="survey-progress__track"
        role="progressbar"
        aria-label={t("survey.answered")}
        aria-valuemin={0}
        aria-valuemax={totalCount}
        aria-valuenow={answeredCount}
        aria-valuetext={t("survey.percent", { percent: percentage })}
      >
        <span className="survey-progress__value" style={{ width: `${percentage}%` }} />
      </div>
    </section>
  );
}
import { useI18n } from "../../i18n/context";
