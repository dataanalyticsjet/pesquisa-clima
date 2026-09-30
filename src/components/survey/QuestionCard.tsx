import type { SurveyQuestion } from "../../data/mockSurvey";
import { LikertScale } from "./LikertScale";

type QuestionCardProps = {
  question: SurveyQuestion;
  questionNumber: number;
  totalQuestions: number;
  selectedValue?: number;
  onAnswer: (value: number) => void;
};

export function QuestionCard({ question, questionNumber, totalQuestions, selectedValue, onAnswer }: QuestionCardProps) {
  return (
    <section className="question-card" aria-labelledby="current-question-title">
      <p className="question-card__count">Pergunta {questionNumber} <span>de {totalQuestions}</span></p>
      <h1 id="current-question-title">{question.text}</h1>
      <LikertScale questionId={question.id} onChange={onAnswer} selectedValue={selectedValue} />
    </section>
  );
}
