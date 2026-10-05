import type { ManagementPillar } from "../../services/management";
import { useI18n } from "../../i18n/context";
import { sectionLabel } from "../../i18n/survey.zh";

export function ManagementPillarApiCard({
  pillar,
  minGroupSize,
}: {
  pillar: ManagementPillar;
  minGroupSize: number;
}) {
  const { locale, t } = useI18n();
  const formatIndex = new Intl.NumberFormat(locale === "zh" ? "zh-CN" : "pt-BR", { maximumFractionDigits: 2 });
  const index = pillar.analytics_available ? pillar.index : null;
  const hasIndex = index !== null;
  const title = sectionLabel(pillar.code, pillar.title, locale);
  const unavailableTitle = pillar.respondent_count === 0 ? t("management.noResponses") : t("management.insufficient");
  const unavailableDescription = pillar.respondent_count === 0
    ? t("management.awaitingIndex")
    : !pillar.analytics_available
      ? `${t("management.minimum", { count: minGroupSize })}.`
      : t("management.indexUnavailable");

  return (
    <article className="pillar-score-card management-pillar-api-card">
      <div className="pillar-score-card__top">
        <div className="management-pillar-api-card__heading">
          <h2>{title}</h2>
          <p className="management-pillar-api-card__questions">
            {pillar.question_count} {pillar.question_count === 1 ? t("management.questionOne") : t("management.questionMany")}
          </p>
        </div>
        {hasIndex ? (
          <div
            className="pillar-score-card__score"
            aria-label={t("management.indexValue", { value: formatIndex.format(index) })}
          >
            <strong>{formatIndex.format(index)}</strong>
            <span>/ 100</span>
          </div>
        ) : null}
      </div>

      {hasIndex ? (
        <div
          className="pillar-score-card__meter"
          role="meter"
          aria-label={t("management.indexFor", { title })}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={index}
        >
          <span style={{ width: `${index}%` }} />
        </div>
      ) : (
        <div className="management-pillar-api-card__unavailable" role="status">
          <strong>{unavailableTitle}</strong>
          <span>{unavailableDescription}</span>
        </div>
      )}
    </article>
  );
}
