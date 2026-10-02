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

export const Route = createFileRoute("/management/voice")({ component: ManagementVoice });

const surveyCode = "CLIMATE_2026";

function getSurveyStatus(status: string): { label: string; tone: "active" | "neutral" } {
  switch (status) {
    case "DRAFT": return { label: "Rascunho", tone: "neutral" };
    case "ACTIVE": return { label: "Ativa", tone: "active" };
    case "CLOSED": return { label: "Encerrada", tone: "neutral" };
    default: return { label: "Status indisponível", tone: "neutral" };
  }
}

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 403: return "Seu perfil não tem autorização para acessar esta área da Gestão.";
      case 404: return "A pesquisa solicitada não foi encontrada.";
      case 503: return "Sua Voz está temporariamente indisponível. Tente novamente mais tarde.";
      case 0: return "Não foi possível conectar ao serviço. Verifique sua conexão e tente novamente.";
    }
  }
  return "Não foi possível carregar Sua Voz. Tente novamente mais tarde.";
}

function QuestionAvailability({
  question,
  minGroupSize,
}: {
  question: ManagementVoiceCommentsQuestion | ManagementVoiceTermsQuestion;
  minGroupSize: number;
}) {
  if (question.respondent_count === 0) {
    return <p className="management-voice-state" role="status">Sem respostas</p>;
  }

  if (!question.analytics_available || question.respondent_count === null) {
    return (
      <div className="management-voice-state management-voice-state--suppressed" role="status">
        <strong>Dados insuficientes</strong>
        <span>Mínimo de {minGroupSize} respostas necessário</span>
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
  const unavailable = question.respondent_count === 0
    || !question.analytics_available
    || question.respondent_count === null;

  return (
    <section className="voice-answer-card" aria-labelledby={`voice-${question.question_code}`}>
      <p className="management-eyebrow">{question.question_code}</p>
      <h2 id={`voice-${question.question_code}`}>{question.question_text}</h2>
      {!unavailable && <p className="voice-answer-card__privacy">Comentários anônimos · sem autoria ou horário de envio</p>}
      <QuestionAvailability question={question} minGroupSize={minGroupSize} />
      {!unavailable && question.comments.length > 0 && (
        <ul className="voice-comment-list">
          {question.comments.map((comment, index) => (
            <li key={`${question.question_code}-${index}`}>{comment}</li>
          ))}
        </ul>
      )}
      {!unavailable && question.comments.length === 0 && (
        <p className="management-voice-state" role="status">Nenhum comentário disponível.</p>
      )}
    </section>
  );
}

function TermsCard({ question, minGroupSize }: { question: ManagementVoiceTermsQuestion; minGroupSize: number }) {
  const unavailable = question.respondent_count === 0
    || !question.analytics_available
    || question.respondent_count === null;

  return (
    <section className="management-section voice-terms-section" aria-labelledby="voice-Q42">
      <div className="management-section__heading">
        <div>
          <p className="management-eyebrow">Q42 · TERMOS FREQUENTES</p>
          <h2 id="voice-Q42">{question.question_text}</h2>
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
        <p className="management-voice-state" role="status">Nenhum termo disponível.</p>
      )}
    </section>
  );
}

function ManagementVoice() {
  const navigate = useNavigate();
  const [data, setData] = useState<ManagementVoiceResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

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
        setError(getErrorMessage(reason));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [navigate]);

  const status = data ? getSurveyStatus(data.survey_status) : undefined;
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
        title="Sua Voz"
        description="Comentários e termos anônimos das respostas abertas da Pesquisa de Clima."
        statusBadge={status?.label}
        statusTone={status?.tone}
      />

      {loading && (
        <div className="management-pillars-state" role="status" aria-live="polite">
          <span className="management-pillars-state__spinner" aria-hidden="true" />
          <span>Carregando respostas anônimas…</span>
        </div>
      )}
      {!loading && error && <p className="management-pillars-state management-pillars-state--error" role="alert">{error}</p>}
      {!loading && data && (
        <>
          <p className="management-privacy-note">
            <span className="management-privacy-note__icon" aria-hidden="true">i</span>
            <span>Comentários anônimos, sem identificadores técnicos ou indicação da ordem de envio.</span>
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
