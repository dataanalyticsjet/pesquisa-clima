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
import { useI18n } from "../../i18n/context";
import type { TranslationKey } from "../../i18n/catalog";
import { localizedSurvey } from "../../i18n/survey.zh";

function hasAnswer(value: SurveyAnswer | undefined) {
  return (typeof value === "number") || (typeof value === "string" && value.trim().length > 0) || (Array.isArray(value) && value.length > 0);
}

function answerIsReady(_question: { optionSource?: string }, value: SurveyAnswer | undefined) {
  return hasAnswer(value);
}

function toSubmissionAnswers(survey: SurveyDefinition, answers: Record<string, SurveyAnswer>): SurveySubmissionAnswer[] {
  const payload: SurveySubmissionAnswer[] = [];
  for (const question of survey.questions) {
    const value = answers[question.id];
    if (!hasAnswer(value)) continue;
    const questionCode = question.id.toUpperCase();
    if (question.type === "textarea" || question.type === "short_text") {
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
  const [regionalError, setRegionalError] = useState<TranslationKey | "">("");
  const [serviceCentersError, setServiceCentersError] = useState<TranslationKey | "">("");
  const [confirming, setConfirming] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<TranslationKey | "">("");
  const [submitErrorQuestionCode, setSubmitErrorQuestionCode] = useState<string | null>(null);
  const [submitState, setSubmitState] = useState<"ready" | "success" | "completed">("ready");
  const { locale, t } = useI18n();
  const displaySurvey = useMemo(() => localizedSurvey(survey, locale), [survey, locale]);
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
      if (active) setRegionalError(error instanceof ApiError && error.status === 401 ? "survey.sessionExpired" : "survey.regionalsError");
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
      if (active) setServiceCentersError(error instanceof ApiError && error.status === 401 ? "survey.sessionExpired" : "survey.basesError");
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
    setSubmitErrorQuestionCode(null);
    try {
      await submitSurveyResponses(survey.code, toSubmissionAnswers(survey, answers));
      setConfirming(false);
      setSubmitState("success");
      void getParticipationStatus(survey.code).catch(() => undefined);
    } catch (error) {
      setConfirming(false);
      if (error instanceof ApiError && error.status === 409 && error.code === "SURVEY_ALREADY_COMPLETED") {
        setSubmitState("completed");
      } else if (error instanceof ApiError && error.status === 409 && error.code === "SURVEY_NOT_ACTIVE") {
        setSubmitError("survey.notActive");
      } else if (error instanceof ApiError && error.status === 422) {
        const rejectedQuestion = questions.find((question) => question.id === error.questionCode);
        if (rejectedQuestion) {
          setSubmitError("survey.invalidQuestion");
          setSubmitErrorQuestionCode(rejectedQuestion.id);
        } else {
          setSubmitError("survey.invalidAnswers");
        }
      } else {
        setSubmitError("survey.submitError");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (submitState === "success") return <SurveySuccess completionText={displaySurvey.completion_text} />;
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

  function returnToRejectedQuestion() {
    const questionIndex = questions.findIndex((question) => question.id === submitErrorQuestionCode);
    if (questionIndex < 0) return;
    setCurrentQuestionIndex(questionIndex);
    setStep("questions");
    setSubmitError("");
    setSubmitErrorQuestionCode(null);
  }

  const currentOptions = currentQuestion?.optionSource === "ORG_REGIONAL" ? regionals : currentQuestion?.optionSource === "ORG_BASE" ? serviceCenters : undefined;
  const optionsLoading = currentQuestion?.optionSource === "ORG_REGIONAL" ? regionalLoading : currentQuestion?.optionSource === "ORG_BASE" ? serviceCentersLoading : false;
  const optionsErrorKey = currentQuestion?.optionSource === "ORG_REGIONAL" ? regionalError : currentQuestion?.optionSource === "ORG_BASE" ? serviceCentersError : "";
  const optionsError = optionsErrorKey ? t(optionsErrorKey) : "";
  const displayQuestion = displaySurvey.questions[currentQuestionIndex];
  const optionsDisabled = currentQuestion?.optionSource === "ORG_BASE" && !selectedRegional;

  return (
    <div className="survey-flow">
      <header className="survey-flow__header">
        <Link className="survey-back-link" to="/home"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M19 12H5m6 6-6-6 6-6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg>{t("survey.backHome")}</Link>
        <div className="survey-flow__title-row"><div><p className="survey-section-eyebrow">{t("survey.eyebrow")}</p>{step !== "intro" && <h1>{displaySurvey.title}</h1>}</div><span className="survey-demo-label">{survey.status === "DRAFT" ? t("survey.draft") : t("survey.active")}</span></div>
      </header>
      {step === "intro" && <SurveyIntro survey={displaySurvey} onStart={() => setStep("questions")} />}
      {step === "questions" && currentQuestion && <div className="survey-question-stage">
        <SurveyProgress answeredCount={answeredCount} totalCount={questionCount} />
        <SectionProgress answers={answers} currentSectionIndex={displaySurvey.sections.findIndex((section) => section.id === currentQuestion.sectionId)} survey={displaySurvey} />
        <QuestionCard onAnswer={answerCurrent} question={displayQuestion} questionNumber={currentQuestion.number} selectedValue={currentAnswer} totalQuestions={questionCount} optionsOverride={currentOptions} optionsLoading={optionsLoading} optionsDisabled={optionsDisabled} optionsError={optionsError} navigation={<nav className="survey-question-navigation" aria-label={t("survey.questionNav")}>
          <button className="survey-button survey-button--secondary" onClick={goBack} type="button">{t("survey.back")}</button>
          {currentQuestionIndex === questionCount - 1 ? <button className="survey-button survey-button--primary" disabled={(currentQuestion.required && !answerIsReady(currentQuestion, currentAnswer)) || !canReview} onClick={goForward} type="button">{t("survey.review")}</button> : <button className="survey-button survey-button--primary" disabled={(currentQuestion.required && !answerIsReady(currentQuestion, currentAnswer)) || (currentQuestion.optionSource === "ORG_REGIONAL" && (regionalLoading || Boolean(regionalError))) || (currentQuestion.optionSource === "ORG_BASE" && (!selectedRegional || serviceCentersLoading || Boolean(serviceCentersError)))} onClick={goForward} type="button">{t("survey.next")}<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14m-6-6 6 6-6 6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg></button>}
        </nav>} />
      </div>}
      {step === "review" && <div className="survey-review-stage">
        <SurveyProgress answeredCount={answeredCount} totalCount={questionCount} />
        <SurveyReview answers={answers} onEditSection={editSection} survey={displaySurvey} />
        {submitError && <p className="survey-submit-error" role="alert">{t(submitError, { code: submitErrorQuestionCode ?? "" })}</p>}
        {submitErrorQuestionCode && <button className="survey-button survey-button--secondary" onClick={returnToRejectedQuestion} type="button">{t("survey.retryQuestion", { code: submitErrorQuestionCode })}</button>}
        <div className="survey-review-stage__actions">
          <button className="survey-button survey-button--secondary" onClick={() => { setCurrentQuestionIndex(questionCount - 1); setStep("questions"); }} type="button">{t("survey.backQuestions")}</button>
          <button className="survey-button survey-button--primary" disabled={!canReview || submitting} onClick={() => { setSubmitError(""); setSubmitErrorQuestionCode(null); setConfirming(true); }} type="button">{t("survey.submit")}</button>
        </div>
      </div>}
      {confirming && <SubmitConfirmationDialog isSubmitting={submitting} onCancel={() => { if (!submitting) setConfirming(false); }} onConfirm={() => { void confirmSubmission(); }} />}
    </div>
  );
}
