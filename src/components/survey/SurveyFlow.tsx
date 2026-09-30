import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { mockSurvey } from "../../data/mockSurvey";
import { useSurveyDemo } from "./SurveyDemoContext";
import { PillarProgress } from "./PillarProgress";
import { QuestionCard } from "./QuestionCard";
import { SubmitConfirmationDialog } from "./SubmitConfirmationDialog";
import { SurveyIntro } from "./SurveyIntro";
import { SurveyProgress } from "./SurveyProgress";
import { SurveyReview } from "./SurveyReview";
import { SurveySuccess } from "./SurveySuccess";

const questions = mockSurvey.pillars.flatMap((pillar, pillarIndex) =>
  pillar.questions.map((question) => ({ ...question, pillarIndex })),
);

export function SurveyFlow() {
  const {
    answers,
    completeSurvey,
    currentQuestionIndex,
    isCompleted,
    setAnswer,
    setCurrentQuestionIndex,
    setStep,
    step,
  } = useSurveyDemo();
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const currentQuestion = questions[currentQuestionIndex];
  const questionCount = questions.length;
  const answeredCount = questions.filter((question) => answers[question.id] !== undefined).length;
  const currentAnswer = currentQuestion ? answers[currentQuestion.id] : undefined;
  const canReview = answeredCount === questionCount;

  function goBack() {
    if (currentQuestionIndex === 0) {
      setStep("intro");
      return;
    }
    setCurrentQuestionIndex(currentQuestionIndex - 1);
  }

  function goForward() {
    if (currentAnswer === undefined) return;
    if (currentQuestionIndex < questionCount - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      return;
    }
    if (canReview) setStep("review");
  }

  function editPillar(pillarIndex: number) {
    const firstQuestionIndex = questions.findIndex((question) => question.pillarIndex === pillarIndex);
    if (firstQuestionIndex >= 0) setCurrentQuestionIndex(firstQuestionIndex);
    setStep("questions");
  }

  function confirmSubmission() {
    setConfirmationOpen(false);
    completeSurvey();
  }

  if (isCompleted || step === "success") {
    return (
      <div className="survey-flow survey-flow--success">
        <SurveySuccess />
      </div>
    );
  }

  return (
    <div className="survey-flow">
      <header className="survey-flow__header">
        <Link className="survey-back-link" to="/home">
          <svg aria-hidden="true" viewBox="0 0 24 24">
            <path d="M19 12H5m6 6-6-6 6-6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
          </svg>
          Voltar ao início
        </Link>
        <div className="survey-flow__title-row">
          <div>
            <p className="survey-section-eyebrow">Pesquisa do colaborador</p>
            <h1>{mockSurvey.title}</h1>
          </div>
          <span className="survey-demo-label">Demonstração</span>
        </div>
      </header>

      {step === "intro" && (
        <SurveyIntro onStart={() => setStep("questions")} />
      )}

      {step === "questions" && currentQuestion && (
        <div className="survey-question-stage">
          <SurveyProgress answeredCount={answeredCount} totalCount={questionCount} />
          <div className="survey-pillar-context">
            <PillarProgress answers={answers} currentPillarIndex={currentQuestion.pillarIndex} />
            <div className="survey-pillar-context__current">
              <span>Pilar {currentQuestion.pillarIndex + 1} de {mockSurvey.pillars.length}</span>
              <strong>{mockSurvey.pillars[currentQuestion.pillarIndex].name}</strong>
            </div>
          </div>

          <QuestionCard
            onAnswer={(value) => setAnswer(currentQuestion.id, value)}
            question={currentQuestion}
            questionNumber={currentQuestionIndex + 1}
            selectedValue={currentAnswer}
            totalQuestions={questionCount}
          />

          <nav className="survey-question-navigation" aria-label="Navegação das perguntas">
            <button className="survey-button survey-button--secondary" onClick={goBack} type="button">
              Voltar
            </button>
            {currentQuestionIndex === questionCount - 1 ? (
              <button className="survey-button survey-button--primary" disabled={currentAnswer === undefined || !canReview} onClick={goForward} type="button">
                Revisar respostas
              </button>
            ) : (
              <button className="survey-button survey-button--primary" disabled={currentAnswer === undefined} onClick={goForward} type="button">
                Próxima
                <svg aria-hidden="true" viewBox="0 0 24 24">
                  <path d="M5 12h14m-6-6 6 6-6 6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
                </svg>
              </button>
            )}
          </nav>
        </div>
      )}

      {step === "review" && (
        <div className="survey-review-stage">
          <SurveyProgress answeredCount={answeredCount} totalCount={questionCount} />
          <PillarProgress answers={answers} currentPillarIndex={null} />
          <SurveyReview answers={answers} onEditPillar={editPillar} />
          <div className="survey-review-stage__actions">
            <button className="survey-button survey-button--secondary" onClick={() => {
              setCurrentQuestionIndex(questionCount - 1);
              setStep("questions");
            }} type="button">
              Voltar às perguntas
            </button>
            <button className="survey-button survey-button--primary" disabled={!canReview} onClick={() => setConfirmationOpen(true)} type="button">
              Enviar respostas
            </button>
          </div>
        </div>
      )}

      {confirmationOpen && (
        <SubmitConfirmationDialog
          onCancel={() => setConfirmationOpen(false)}
          onConfirm={confirmSubmission}
        />
      )}
    </div>
  );
}
