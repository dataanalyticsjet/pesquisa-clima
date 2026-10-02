import { Link } from "@tanstack/react-router";
import type { SurveyAnswer } from "../../data/mockSurvey";
import type { SurveyDefinition } from "../../services/surveys";
import { useSurveyDemo } from "./SurveyDemoContext";
import { SectionProgress } from "./SectionProgress";
import { QuestionCard } from "./QuestionCard";
import { SurveyIntro } from "./SurveyIntro";
import { SurveyProgress } from "./SurveyProgress";
import { SurveyReview } from "./SurveyReview";

function hasAnswer(value: SurveyAnswer | undefined) {
  return (typeof value === "number") || (typeof value === "string" && value.trim().length > 0) || (Array.isArray(value) && value.length > 0);
}

export function SurveyFlow({ survey }: { survey: SurveyDefinition }) {
  const { answers, currentQuestionIndex, setAnswer, setCurrentQuestionIndex, setStep, step } = useSurveyDemo();
  const questions = survey.questions;
  const currentQuestion = questions[currentQuestionIndex];
  const questionCount = questions.length;
  const answeredCount = questions.filter((question) => hasAnswer(answers[question.id])).length;
  const currentAnswer = currentQuestion ? answers[currentQuestion.id] : undefined;
  const canReview = questions.filter((question) => question.required).every((question) => hasAnswer(answers[question.id]));

  function goBack() {
    if (currentQuestionIndex === 0) {
      setStep("intro");
      return;
    }
    setCurrentQuestionIndex(currentQuestionIndex - 1);
  }

  function goForward() {
    if (!currentQuestion || (currentQuestion.required && !hasAnswer(currentAnswer))) return;
    if (currentQuestionIndex < questionCount - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      return;
    }
    if (canReview) setStep("review");
  }

  function editSection(sectionIndex: number) {
    const sectionId = survey.sections[sectionIndex]?.id;
    const firstQuestionIndex = questions.findIndex((question) => question.sectionId === sectionId);
    if (firstQuestionIndex >= 0) setCurrentQuestionIndex(firstQuestionIndex);
    setStep("questions");
  }

  return (
    <div className="survey-flow">
      <header className="survey-flow__header">
        <Link className="survey-back-link" to="/home">
          <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M19 12H5m6 6-6-6 6-6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg>
          Voltar ao início
        </Link>
        <div className="survey-flow__title-row">
          <div><p className="survey-section-eyebrow">Pesquisa do colaborador</p>{step !== "intro" && <h1>{survey.title}</h1>}</div>
          <span className="survey-demo-label">{survey.status === "DRAFT" ? "Em desenvolvimento" : "Pesquisa ativa"}</span>
        </div>
      </header>

      {step === "intro" && <SurveyIntro survey={survey} onStart={() => setStep("questions")} />}

      {step === "questions" && currentQuestion && (
        <div className="survey-question-stage">
          <SurveyProgress answeredCount={answeredCount} totalCount={questionCount} />
          <SectionProgress answers={answers} currentSectionIndex={survey.sections.findIndex((section) => section.id === currentQuestion.sectionId)} survey={survey} />
          <QuestionCard onAnswer={(value) => setAnswer(currentQuestion.id, value)} question={currentQuestion} questionNumber={currentQuestion.number} selectedValue={currentAnswer} totalQuestions={questionCount} />
          <nav className="survey-question-navigation" aria-label="Navegação das perguntas">
            <button className="survey-button survey-button--secondary" onClick={goBack} type="button">Voltar</button>
            {currentQuestionIndex === questionCount - 1 ? (
              <button className="survey-button survey-button--primary" disabled={(currentQuestion.required && !hasAnswer(currentAnswer)) || !canReview} onClick={goForward} type="button">Revisar respostas</button>
            ) : (
              <button className="survey-button survey-button--primary" disabled={currentQuestion.required && !hasAnswer(currentAnswer)} onClick={goForward} type="button">
                Próxima<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14m-6-6 6 6-6 6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg>
              </button>
            )}
          </nav>
        </div>
      )}

      {step === "review" && (
        <div className="survey-review-stage">
          <SurveyProgress answeredCount={answeredCount} totalCount={questionCount} />
          <SurveyReview answers={answers} onEditSection={editSection} survey={survey} />
          <div className="survey-review-stage__actions">
            <button className="survey-button survey-button--secondary" onClick={() => { setCurrentQuestionIndex(questionCount - 1); setStep("questions"); }} type="button">Voltar às perguntas</button>
            <button className="survey-button survey-button--primary" disabled type="button">Enviar respostas</button>
          </div>
          <p className="survey-submit-note">O envio estará disponível quando a etapa de submissão for liberada.</p>
        </div>
      )}
    </div>
  );
}
