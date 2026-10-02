import { useEffect, useMemo, useState } from "react";
import { Link } from "@tanstack/react-router";
import type { SurveyAnswer, SurveyOption } from "../../data/mockSurvey";
import type { SurveyDefinition } from "../../services/surveys";
import { ApiError } from "../../lib/api";
import { getOrganizationRegionals, getOrganizationServiceCenters, getParticipationStatus, submitSurveyResponses, type SurveySubmissionAnswer } from "../../services/surveys";
import { useSurveyDemo } from "./SurveyDemoContext";
import { SectionProgress } from "./SectionProgress";
import { QuestionCard } from "./QuestionCard";
import { SurveyIntro } from "./SurveyIntro";
import { SurveyProgress } from "./SurveyProgress";
import { SurveyReview } from "./SurveyReview";
import { SubmitConfirmationDialog } from "./SubmitConfirmationDialog";
import { SurveyAlreadyCompleted } from "./SurveyAlreadyCompleted";
import { SurveySuccess } from "./SurveySuccess";

function hasAnswer(value: SurveyAnswer | undefined) {
  return (typeof value === "number") || (typeof value === "string" && value.trim().length > 0) || (Array.isArray(value) && value.length > 0);
}

function isCnpjFormat(value: string) {
  const normalized = value.replace(/[.\/\-\s]/g, "").toUpperCase();
  return /^[A-Z0-9]{12}\d{2}$/.test(normalized);
}

function answerIsReady(question: { optionSource?: string }, value: SurveyAnswer | undefined) {
  if (!hasAnswer(value)) return false;
  if (question.optionSource === "ORG_CNPJ" && value !== "unknown") return typeof value === "string" && isCnpjFormat(value);
  return true;
}

function toSubmissionAnswers(survey: SurveyDefinition, answers: Record<string, SurveyAnswer>): SurveySubmissionAnswer[] {
  const payload: SurveySubmissionAnswer[] = [];
  for (const question of survey.questions) {
    const value = answers[question.id];
    if (!hasAnswer(value)) continue;
    const questionCode = question.id.toUpperCase();
    if (question.optionSource === "ORG_CNPJ") {
      payload.push(value === "unknown"
        ? { question_code: questionCode, option_codes: ["unknown"] }
        : { question_code: questionCode, text_value: String(value) });
    } else if (question.type === "textarea" || question.type === "short_text") {
      payload.push({ question_code: questionCode, text_value: String(value) });
    } else {
      payload.push({ question_code: questionCode, option_codes: Array.isArray(value) ? value.map(String) : [String(value)] });
    }
  }
  return payload;
}

export function SurveyFlow({ survey }: { survey: SurveyDefinition }) {
  const { answers, currentQuestionIndex, setAnswer, setCurrentQuestionIndex, setStep, step } = useSurveyDemo();
  const [regionals, setRegionals] = useState<SurveyOption[]>([]);
  const [serviceCenters, setServiceCenters] = useState<SurveyOption[]>([]);
  const [regionalLoading, setRegionalLoading] = useState(false);
  const [serviceCentersLoading, setServiceCentersLoading] = useState(false);
  const [regionalError, setRegionalError] = useState("");
  const [serviceCentersError, setServiceCentersError] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [submitState, setSubmitState] = useState<"ready" | "success" | "completed">("ready");
  const questions = survey.questions;
  const currentQuestion = questions[currentQuestionIndex];
  const questionCount = questions.length;
  const answeredCount = questions.filter((question) => hasAnswer(answers[question.id])).length;
  const currentAnswer = currentQuestion ? answers[currentQuestion.id] : undefined;
  const regionalQuestion = useMemo(() => questions.find((question) => question.optionSource === "ORG_REGIONAL"), [questions]);
  const serviceCenterQuestion = useMemo(() => questions.find((question) => question.optionSource === "ORG_BASE"), [questions]);
  const selectedRegional = regionalQuestion && typeof answers[regionalQuestion.id] === "string" ? answers[regionalQuestion.id] as string : "";
  const canReview = questions.filter((question) => question.required).every((question) => answerIsReady(question, answers[question.id]));

  useEffect(() => {
    let active = true;
    setRegionalLoading(true);
    getOrganizationRegionals().then((result) => {
      if (active) setRegionals(result.regionals.map((item) => ({ value: item.code, label: item.label })));
    }).catch((error: unknown) => {
      if (active) setRegionalError(error instanceof ApiError && error.status === 401 ? "Sua sessão expirou. Atualize a página e entre novamente." : "Não foi possível carregar as Regionais. Tente novamente.");
    }).finally(() => { if (active) setRegionalLoading(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    setServiceCenters([]);
    setServiceCentersError("");
    if (!selectedRegional) { setServiceCentersLoading(false); return () => { active = false; }; }
    setServiceCentersLoading(true);
    getOrganizationServiceCenters(selectedRegional).then((result) => {
      if (active) setServiceCenters(result.service_centers.map((item) => ({ value: item.code, label: item.display_name })));
    }).catch((error: unknown) => {
      if (active) setServiceCentersError(error instanceof ApiError && error.status === 401 ? "Sua sessão expirou. Atualize a página e entre novamente." : "Não foi possível carregar as unidades desta Regional.");
    }).finally(() => { if (active) setServiceCentersLoading(false); });
    return () => { active = false; };
  }, [selectedRegional]);

  function answerCurrent(value: SurveyAnswer) {
    if (!currentQuestion) return;
    setAnswer(currentQuestion.id, value);
    if (currentQuestion.optionSource === "ORG_REGIONAL" && serviceCenterQuestion) setAnswer(serviceCenterQuestion.id, "");
  }

  async function confirmSubmission() {
    if (submitting || !canReview) return;
    setSubmitting(true);
    setSubmitError("");
    try {
      await submitSurveyResponses(survey.code, toSubmissionAnswers(survey, answers));
      setConfirming(false);
      setSubmitState("success");
      void getParticipationStatus(survey.code).catch(() => undefined);
    } catch (error) {
      if (error instanceof ApiError && error.status === 409 && error.code === "SURVEY_ALREADY_COMPLETED") {
        setConfirming(false);
        setSubmitState("completed");
      } else if (error instanceof ApiError && error.status === 409 && error.code === "SURVEY_NOT_ACTIVE") {
        setSubmitError("Esta pesquisa ainda não está aberta para envio. Suas respostas não foram enviadas.");
      } else if (error instanceof ApiError && error.status === 422) {
        setSubmitError("Não foi possível validar as respostas. Confira o CNPJ e as opções selecionadas e tente novamente.");
      } else {
        setSubmitError("Não foi possível enviar as respostas agora. Tente novamente mais tarde.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (submitState === "success") return <SurveySuccess completionText={survey.completion_text} />;
  if (submitState === "completed") return <SurveyAlreadyCompleted />;

  function goBack() {
    if (currentQuestionIndex === 0) { setStep("intro"); return; }
    setCurrentQuestionIndex(currentQuestionIndex - 1);
  }

  function goForward() {
    if (!currentQuestion || (currentQuestion.required && !answerIsReady(currentQuestion, currentAnswer))) return;
    if (currentQuestionIndex < questionCount - 1) { setCurrentQuestionIndex(currentQuestionIndex + 1); return; }
    if (canReview) setStep("review");
  }

  function editSection(sectionIndex: number) {
    const sectionId = survey.sections[sectionIndex]?.id;
    const firstQuestionIndex = questions.findIndex((question) => question.sectionId === sectionId);
    if (firstQuestionIndex >= 0) setCurrentQuestionIndex(firstQuestionIndex);
    setStep("questions");
  }

  const currentOptions = currentQuestion?.optionSource === "ORG_REGIONAL" ? regionals : currentQuestion?.optionSource === "ORG_BASE" ? serviceCenters : undefined;
  const optionsLoading = currentQuestion?.optionSource === "ORG_REGIONAL" ? regionalLoading : currentQuestion?.optionSource === "ORG_BASE" ? serviceCentersLoading : false;
  const optionsError = currentQuestion?.optionSource === "ORG_REGIONAL" ? regionalError : currentQuestion?.optionSource === "ORG_BASE" ? serviceCentersError : "";
  const optionsDisabled = currentQuestion?.optionSource === "ORG_BASE" && !selectedRegional;

  return (
    <div className="survey-flow">
      <header className="survey-flow__header">
        <Link className="survey-back-link" to="/home"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M19 12H5m6 6-6-6 6-6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg>Voltar ao início</Link>
        <div className="survey-flow__title-row"><div><p className="survey-section-eyebrow">Pesquisa do colaborador</p>{step !== "intro" && <h1>{survey.title}</h1>}</div><span className="survey-demo-label">{survey.status === "DRAFT" ? "Em desenvolvimento" : "Pesquisa ativa"}</span></div>
      </header>
      {step === "intro" && <SurveyIntro survey={survey} onStart={() => setStep("questions")} />}
      {step === "questions" && currentQuestion && <div className="survey-question-stage">
        <SurveyProgress answeredCount={answeredCount} totalCount={questionCount} />
        <SectionProgress answers={answers} currentSectionIndex={survey.sections.findIndex((section) => section.id === currentQuestion.sectionId)} survey={survey} />
        <QuestionCard onAnswer={answerCurrent} question={currentQuestion} questionNumber={currentQuestion.number} selectedValue={currentAnswer} totalQuestions={questionCount} optionsOverride={currentOptions} optionsLoading={optionsLoading} optionsDisabled={optionsDisabled} optionsError={optionsError} />
        <nav className="survey-question-navigation" aria-label="Navegação das perguntas">
          <button className="survey-button survey-button--secondary" onClick={goBack} type="button">Voltar</button>
          {currentQuestionIndex === questionCount - 1 ? <button className="survey-button survey-button--primary" disabled={(currentQuestion.required && !answerIsReady(currentQuestion, currentAnswer)) || !canReview} onClick={goForward} type="button">Revisar respostas</button> : <button className="survey-button survey-button--primary" disabled={(currentQuestion.required && !answerIsReady(currentQuestion, currentAnswer)) || (currentQuestion.optionSource === "ORG_REGIONAL" && (regionalLoading || Boolean(regionalError))) || (currentQuestion.optionSource === "ORG_BASE" && (!selectedRegional || serviceCentersLoading || Boolean(serviceCentersError)))} onClick={goForward} type="button">Próxima<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14m-6-6 6 6-6 6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg></button>}
        </nav>
      </div>}
      {step === "review" && <div className="survey-review-stage">
        <SurveyProgress answeredCount={answeredCount} totalCount={questionCount} />
        <SurveyReview answers={answers} onEditSection={editSection} survey={survey} />
        {submitError && <p className="survey-submit-error" role="alert">{submitError}</p>}
        <div className="survey-review-stage__actions">
          <button className="survey-button survey-button--secondary" onClick={() => { setCurrentQuestionIndex(questionCount - 1); setStep("questions"); }} type="button">Voltar às perguntas</button>
          <button className="survey-button survey-button--primary" disabled={!canReview || submitting} onClick={() => { setSubmitError(""); setConfirming(true); }} type="button">Enviar respostas</button>
        </div>
      </div>}
      {confirming && <SubmitConfirmationDialog isSubmitting={submitting} onCancel={() => { if (!submitting) setConfirming(false); }} onConfirm={() => { void confirmSubmission(); }} />}
    </div>
  );
}
