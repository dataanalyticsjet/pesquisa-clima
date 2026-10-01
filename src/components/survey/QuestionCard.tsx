import { mockSurvey, type SurveyAnswer, type SurveyQuestion } from "../../data/mockSurvey";
import type { ChangeEvent } from "react";
import { LikertScale } from "./LikertScale";

type QuestionCardProps = {
  question: SurveyQuestion;
  questionNumber: number;
  totalQuestions: number;
  selectedValue?: SurveyAnswer;
  onAnswer: (value: SurveyAnswer) => void;
};

function ChoiceOptions({ question, selectedValue, onAnswer }: Omit<QuestionCardProps, "questionNumber" | "totalQuestions">) {
  const options = question.options ?? [];
  if (question.type === "select") {
    return (
      <label className="survey-select-field">
        <span className="visually-hidden">{question.text}</span>
        <select aria-label={question.text} onChange={(event) => onAnswer(event.target.value)} value={typeof selectedValue === "string" ? selectedValue : ""}>
          <option disabled value="">{question.placeholder ?? "Selecione uma opção"}</option>
          {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      </label>
    );
  }

  if (question.type === "multiple_choice") {
    const selected = Array.isArray(selectedValue) ? selectedValue : [];
    return (
      <fieldset className="survey-choice-list survey-choice-list--multiple">
        <legend className="visually-hidden">{question.helperText ?? "Selecione uma ou mais opções"}</legend>
        {options.map((option) => {
          const checked = selected.includes(option.value);
          return (
            <label className="survey-choice" key={option.value}>
              <input
                checked={checked}
                onChange={() => {
                  if (option.exclusive) {
                    onAnswer(checked ? [] : [option.value]);
                  } else {
                    const withoutExclusive = selected.filter((value) => !options.find((item) => item.value === value)?.exclusive);
                    onAnswer(checked ? withoutExclusive.filter((value) => value !== option.value) : [...withoutExclusive, option.value]);
                  }
                }}
                type="checkbox"
                value={option.value}
              />
              <span>{option.label}</span>
            </label>
          );
        })}
      </fieldset>
    );
  }

  return (
    <fieldset className="survey-choice-list">
      <legend className="visually-hidden">{question.helperText ?? "Selecione uma opção"}</legend>
      {options.map((option) => (
        <label className="survey-choice" key={option.value}>
          <input checked={selectedValue === option.value} name={`answer-${question.id}`} onChange={() => onAnswer(option.value)} type="radio" value={option.value} />
          <span>{option.label}</span>
        </label>
      ))}
    </fieldset>
  );
}

function NpsScale({ question, selectedValue, onAnswer }: Omit<QuestionCardProps, "questionNumber" | "totalQuestions">) {
  return (
    <fieldset className="nps-scale">
      <legend>Selecione uma nota de 0 a 10</legend>
      <div className="nps-scale__options">
        {Array.from({ length: 11 }, (_, value) => (
          <label className="nps-option" key={value}>
            <input checked={selectedValue === value} name={`answer-${question.id}`} onChange={() => onAnswer(value)} type="radio" value={value} />
            <span>{value}</span>
          </label>
        ))}
      </div>
      <div className="nps-scale__captions"><span>0 — {mockSurvey.npsLabels.low}</span><span>10 — {mockSurvey.npsLabels.high}</span></div>
    </fieldset>
  );
}

function TextAnswer({ question, selectedValue, onAnswer }: Omit<QuestionCardProps, "questionNumber" | "totalQuestions">) {
  const value = typeof selectedValue === "string" ? selectedValue : "";
  const common = {
    "aria-label": question.text,
    onChange: (event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => onAnswer(event.target.value),
    placeholder: question.placeholder,
    value,
  };
  return question.type === "short_text"
    ? <input className="survey-text-input" {...common} />
    : <textarea className="survey-textarea" rows={5} {...common} />;
}

export function QuestionCard({ question, questionNumber, totalQuestions, selectedValue, onAnswer }: QuestionCardProps) {
  return (
    <section className="question-card" aria-labelledby="current-question-title">
      <p className="question-card__count">Pergunta {questionNumber} <span>de {totalQuestions}</span></p>
      <h1 id="current-question-title">{question.text}</h1>
      {question.helperText && <p className="question-card__helper">{question.helperText}</p>}
      {question.type === "likert" && <LikertScale questionId={question.id} onChange={onAnswer} selectedValue={typeof selectedValue === "number" ? selectedValue : undefined} />}
      {(question.type === "select" || question.type === "single_choice" || question.type === "multiple_choice") && <ChoiceOptions onAnswer={onAnswer} question={question} selectedValue={selectedValue} />}
      {question.type === "nps" && <NpsScale onAnswer={onAnswer} question={question} selectedValue={selectedValue} />}
      {(question.type === "textarea" || question.type === "short_text") && <TextAnswer onAnswer={onAnswer} question={question} selectedValue={selectedValue} />}
    </section>
  );
}
