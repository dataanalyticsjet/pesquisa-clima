import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { ApiError } from "../lib/api";
import {
  getManagementVoice,
  type ManagementVoiceCommentsQuestion,
  type ManagementVoiceResponse,
  type ManagementVoiceTermsQuestion,
} from "../services/management";
import { useI18n } from "../i18n/context";
import type { TranslationKey } from "../i18n/catalog";
import { questionText } from "../i18n/survey.zh";

export const Route = createFileRoute("/management/voice")({ component: ManagementVoice });

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
      case 403: return "management.voiceForbidden";
      case 404: return "management.surveyNotFound";
      case 503: return "management.voiceUnavailable";
      case 0: return "management.connectionError";
    }
  }
  return "management.voiceLoadError";
}

function QuestionAvailability({
  question,
  minGroupSize,
}: {
  question: ManagementVoiceCommentsQuestion | ManagementVoiceTermsQuestion;
  minGroupSize: number;
}) {
  const { t } = useI18n();
  if (question.respondent_count === 0) {
    return <p className="management-voice-state" role="status">{t("management.noResponses")}</p>;
  }

  if (!question.analytics_available || question.respondent_count === null) {
    return (
      <div className="management-voice-state management-voice-state--suppressed" role="status">
        <strong>{t("management.insufficient")}</strong>
        <span>{t("management.minimum", { count: minGroupSize })}</span>
      </div>
    );
  }

  return null;
}

function CommentsCard({
  question,
  minGroupSize,
}: {
  question: ManagementVoiceCommentsQuestion;
  minGroupSize: number;
}) {
  const { locale, t } = useI18n();
  const unavailable = question.respondent_count === 0
    || !question.analytics_available
    || question.respondent_count === null;

  return (
    <section className="voice-answer-card" aria-labelledby={`voice-${question.question_code}`}>
      <p className="management-eyebrow">{question.question_code}</p>
      <h2 id={`voice-${question.question_code}`}>{questionText(question.question_code, question.question_text, locale)}</h2>
      {!unavailable && <p className="voice-answer-card__privacy">{t("management.voicePrivacy")}</p>}
      <QuestionAvailability question={question} minGroupSize={minGroupSize} />
      {!unavailable && question.comments.length > 0 && (
        <ul className="voice-comment-list">
          {question.comments.map((comment, index) => (
            <li key={`${question.question_code}-${index}`}>{comment}</li>
          ))}
        </ul>
      )}
      {!unavailable && question.comments.length === 0 && (
        <p className="management-voice-state" role="status">{t("management.noComment")}</p>
      )}
    </section>
  );
}

function TermsCard({ question, minGroupSize }: { question: ManagementVoiceTermsQuestion; minGroupSize: number }) {
  const { locale, t } = useI18n();
  const unavailable = question.respondent_count === 0
    || !question.analytics_available
    || question.respondent_count === null;

  return (
    <section className="management-section voice-terms-section" aria-labelledby="voice-Q42">
      <div className="management-section__heading">
        <div>
          <p className="management-eyebrow">{t("management.frequentTerms")}</p>
          <h2 id="voice-Q42">{questionText(question.question_code, question.question_text, locale)}</h2>
        </div>
      </div>
      <QuestionAvailability question={question} minGroupSize={minGroupSize} />
      {!unavailable && question.terms.length > 0 && (
        <ul className="voice-terms-list">
          {question.terms.map((item) => (
            <li key={item.term}>
              <span>{item.term}</span>
              <strong>{item.count}</strong>
            </li>
          ))}
        </ul>
      )}
      {!unavailable && question.terms.length === 0 && (
        <p className="management-voice-state" role="status">{t("management.noTerm")}</p>
      )}
    </section>
  );
}

function ManagementVoice() {
  const navigate = useNavigate();
  const [data, setData] = useState<ManagementVoiceResponse | null>(null);
  const [error, setError] = useState<TranslationKey | "">("");
  const [loading, setLoading] = useState(true);
  const { t } = useI18n();

  useEffect(() => {
    let active = true;
    getManagementVoice(surveyCode)
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
  const questions = data?.questions ?? [];
  const commentQuestions = questions.filter((question): question is ManagementVoiceCommentsQuestion =>
    question.question_code === "Q40" || question.question_code === "Q41",
  );
  const termsQuestion = questions.find((question): question is ManagementVoiceTermsQuestion =>
    question.question_code === "Q42",
  );

  return (
    <ManagementLayout>
      <ManagementPageTitle
        title={t("management.voiceTitle")}
        description={t("management.voiceDescription")}
        statusBadge={status?.label}
        statusTone={status?.tone}
      />

      {loading && (
        <div className="management-pillars-state" role="status" aria-live="polite">
          <span className="management-pillars-state__spinner" aria-hidden="true" />
          <span>{t("management.voiceLoading")}</span>
        </div>
      )}
      {!loading && error && <p className="management-pillars-state management-pillars-state--error" role="alert">{t(error)}</p>}
      {!loading && data && (
        <>
          <p className="management-privacy-note">
            <span className="management-privacy-note__icon" aria-hidden="true">i</span>
            <span>{t("management.voicePrivacyNote")}</span>
          </p>
          <div className="voice-answer-grid">
            {commentQuestions.map((question) => (
              <CommentsCard
                key={question.question_code}
                question={question}
                minGroupSize={data.min_group_size}
              />
            ))}
          </div>
          {termsQuestion && <TermsCard question={termsQuestion} minGroupSize={data.min_group_size} />}
        </>
      )}
    </ManagementLayout>
  );
}
