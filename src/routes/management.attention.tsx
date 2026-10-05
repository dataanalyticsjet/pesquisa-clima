import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { ApiError } from "../lib/api";
import {
  getManagementAttention,
  type ManagementAttentionQuestion,
  type ManagementAttentionResponse,
} from "../services/management";
import { useI18n } from "../i18n/context";
import type { TranslationKey } from "../i18n/catalog";
import { questionText } from "../i18n/survey.zh";

export const Route = createFileRoute("/management/attention")({ component: ManagementAttention });

const surveyCode = "CLIMATE_2026";
function getSurveyStatus(status: string, t: ReturnType<typeof useI18n>["t"]): { label: string; tone: "active" | "neutral" } {
  switch (status) {
    case "DRAFT": return { label: t("management.draft"), tone: "neutral" };
    case "ACTIVE": return { label: t("management.active"), tone: "active" };
    case "CLOSED": return { label: t("management.closed"), tone: "neutral" };
    default: return { label: t("management.statusUnavailable"), tone: "neutral" };
  }
}

function getErrorKey(error: unknown): TranslationKey {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 403: return "management.attentionForbidden";
      case 404: return "management.surveyNotFound";
      case 503: return "management.attentionUnavailable";
      case 0: return "management.connectionError";
    }
  }
  return "management.resultsLoadError";
}

function AttentionMetric({
  analyticsAvailable,
  attentionRate,
  respondentCount,
  minGroupSize,
  compact = false,
}: {
  analyticsAvailable: boolean;
  attentionRate: number | null;
  respondentCount: number | null;
  minGroupSize: number;
  compact?: boolean;
}) {
  const { locale, t } = useI18n();
  const formatPercent = new Intl.NumberFormat(locale === "zh" ? "zh-CN" : "pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (respondentCount === 0) {
    return <span className={`management-attention-metric${compact ? " is-compact" : ""}`} role="status">{t("management.noResponses")}</span>;
  }

  if (!analyticsAvailable || attentionRate === null) {
    return (
      <span className={`management-attention-metric management-attention-metric--suppressed${compact ? " is-compact" : ""}`} role="status">
        <strong>{t("management.insufficient")}</strong>
        <small>{t("management.minimum", { count: minGroupSize })}</small>
      </span>
    );
  }

  return (
    <span className={`management-attention-metric${compact ? " is-compact" : ""}`}>
      <small>{t("management.attentionRate")}</small>
      <strong>{formatPercent.format(attentionRate)}%</strong>
    </span>
  );
}

function QuestionList({
  questions,
  minGroupSize,
}: {
  questions: ManagementAttentionQuestion[];
  minGroupSize: number;
}) {
  const { locale, t } = useI18n();
  if (!questions.length) {
    return <p className="management-attention-empty">{t("management.noQuestions")}</p>;
  }

  return (
    <ul className="management-attention-questions">
      {questions.map((question) => (
        <li className="management-attention-question" key={question.question_code}>
          <div className="management-attention-question__copy">
            <span>{question.question_code}</span>
            <p>{questionText(question.question_code, question.question_text, locale)}</p>
          </div>
          <AttentionMetric
            analyticsAvailable={question.analytics_available}
            attentionRate={question.attention_rate}
            respondentCount={question.respondent_count}
            minGroupSize={minGroupSize}
            compact
          />
        </li>
      ))}
    </ul>
  );
}

function RegionalQuestions({
  regional,
  minGroupSize,
}: {
  regional: ManagementAttentionResponse["regionals"][number];
  minGroupSize: number;
}) {
  const { t } = useI18n();
  return (
    <details className="management-attention-questions-disclosure">
      <summary>{t("management.regionalQuestionCount", { count: regional.questions.length })}</summary>
      <QuestionList questions={regional.questions} minGroupSize={minGroupSize} />
    </details>
  );
}

function ManagementAttention() {
  const navigate = useNavigate();
  const [data, setData] = useState<ManagementAttentionResponse | null>(null);
  const [error, setError] = useState<TranslationKey | "">("");
  const [loading, setLoading] = useState(true);
  const { t } = useI18n();

  useEffect(() => {
    let active = true;
    getManagementAttention(surveyCode)
      .then((result) => { if (active) setData(result); })
      .catch((reason: unknown) => {
        if (!active) return;
        if (reason instanceof ApiError && reason.status === 401) {
          void navigate({ to: "/login", replace: true });
          return;
        }
        setError(getErrorKey(reason));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [navigate]);

  const status = data ? getSurveyStatus(data.survey_status, t) : undefined;
  const serviceCenterCount = data?.regionals.reduce((total, regional) => total + regional.scs.length, 0) ?? 0;

  return (
    <ManagementLayout>
      <ManagementPageTitle
        title={t("management.attentionTitle")}
        description={t("management.attentionDescription")}
        statusBadge={status?.label}
        statusTone={status?.tone}
      />

      {loading && (
        <div className="management-pillars-state" role="status" aria-live="polite">
          <span className="management-pillars-state__spinner" aria-hidden="true" />
          <span>{t("management.loadingAttention")}</span>
        </div>
      )}
      {!loading && error && <p className="management-pillars-state management-pillars-state--error" role="alert">{t(error)}</p>}

      {!loading && data && (
        <>
          <p className="management-attention-summary">
            {t("management.allGroups", { regionals: data.regionals.length, scs: serviceCenterCount })}
          </p>
          <div className="management-attention-regionals" aria-label={t("management.allGroupsAria")}>
            {data.regionals.map((regional) => (
              <article className="management-attention-regional" key={regional.regional_code}>
                <header className="management-attention-regional__header">
                  <div>
                    <p className="management-eyebrow">{t("management.regional")}</p>
                    <h2>{regional.regional_code}</h2>
                  </div>
                  <AttentionMetric
                    analyticsAvailable={regional.analytics_available}
                    attentionRate={regional.attention_rate}
                    respondentCount={regional.respondent_count}
                    minGroupSize={data.min_group_size}
                  />
                </header>

                <RegionalQuestions regional={regional} minGroupSize={data.min_group_size} />

                <div className="management-attention-scs" aria-label={t("management.scAria", { code: regional.regional_code })}>
                  {regional.scs.map((sc) => (
                    <details className="management-attention-sc" key={sc.sc_code}>
                      <summary className="management-attention-sc__summary">
                        <span className="management-attention-sc__name">{sc.display_name || `${sc.sc_code} — ${sc.sc_name}`}</span>
                        <AttentionMetric
                          analyticsAvailable={sc.analytics_available}
                          attentionRate={sc.attention_rate}
                          respondentCount={sc.respondent_count}
                          minGroupSize={data.min_group_size}
                          compact
                        />
                      </summary>
                      <QuestionList questions={sc.questions} minGroupSize={data.min_group_size} />
                    </details>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </>
      )}
    </ManagementLayout>
  );
}
