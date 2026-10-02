import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { ApiError } from "../lib/api";
import {
  getManagementAttention,
  type ManagementAttentionQuestion,
  type ManagementAttentionResponse,
} from "../services/management";

export const Route = createFileRoute("/management/attention")({ component: ManagementAttention });

const surveyCode = "CLIMATE_2026";
const formatPercent = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

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
      case 403: return "Seu perfil não tem autorização para acessar os pontos de atenção.";
      case 404: return "A pesquisa solicitada não foi encontrada.";
      case 503: return "Os pontos de atenção estão temporariamente indisponíveis. Tente novamente mais tarde.";
      case 0: return "Não foi possível conectar ao serviço. Verifique sua conexão e tente novamente.";
    }
  }
  return "Não foi possível carregar os pontos de atenção. Tente novamente mais tarde.";
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
  if (respondentCount === 0) {
    return <span className={`management-attention-metric${compact ? " is-compact" : ""}`} role="status">Sem respostas</span>;
  }

  if (!analyticsAvailable || attentionRate === null) {
    return (
      <span className={`management-attention-metric management-attention-metric--suppressed${compact ? " is-compact" : ""}`} role="status">
        <strong>Dados insuficientes</strong>
        <small>Mínimo de {minGroupSize} respostas necessário</small>
      </span>
    );
  }

  return (
    <span className={`management-attention-metric${compact ? " is-compact" : ""}`}>
      <small>Taxa de atenção</small>
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
  if (!questions.length) {
    return <p className="management-attention-empty">Nenhuma pergunta elegível disponível.</p>;
  }

  return (
    <ul className="management-attention-questions">
      {questions.map((question) => (
        <li className="management-attention-question" key={question.question_code}>
          <div className="management-attention-question__copy">
            <span>{question.question_code}</span>
            <p>{question.question_text}</p>
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
  return (
    <details className="management-attention-questions-disclosure">
      <summary>Perguntas da Regional <span>({regional.questions.length})</span></summary>
      <QuestionList questions={regional.questions} minGroupSize={minGroupSize} />
    </details>
  );
}

function ManagementAttention() {
  const navigate = useNavigate();
  const [data, setData] = useState<ManagementAttentionResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

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
        setError(getErrorMessage(reason));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [navigate]);

  const status = data ? getSurveyStatus(data.survey_status) : undefined;
  const serviceCenterCount = data?.regionals.reduce((total, regional) => total + regional.scs.length, 0) ?? 0;

  return (
    <ManagementLayout showDemoFilters={false}>
      <ManagementPageTitle
        title="Pontos de atenção"
        description="Taxas consolidadas por Regional, SC e pergunta, respeitando o mínimo de respostas para divulgação."
        statusBadge={status?.label}
        statusTone={status?.tone}
      />

      {loading && (
        <div className="management-pillars-state" role="status" aria-live="polite">
          <span className="management-pillars-state__spinner" aria-hidden="true" />
          <span>Carregando pontos de atenção…</span>
        </div>
      )}
      {!loading && error && <p className="management-pillars-state management-pillars-state--error" role="alert">{error}</p>}

      {!loading && data && (
        <>
          <p className="management-attention-summary">
            Todos os grupos · {data.regionals.length} Regionais · {serviceCenterCount} SCs
          </p>
          <div className="management-attention-regionals" aria-label="Todos os grupos por Regional">
            {data.regionals.map((regional) => (
              <article className="management-attention-regional" key={regional.regional_code}>
                <header className="management-attention-regional__header">
                  <div>
                    <p className="management-eyebrow">REGIONAL</p>
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

                <div className="management-attention-scs" aria-label={`SCs da Regional ${regional.regional_code}`}>
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
