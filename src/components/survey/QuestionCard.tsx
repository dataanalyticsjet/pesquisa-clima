import type { ReactNode, ChangeEvent } from "react";
import type { SurveyAnswer, SurveyOption, SurveyQuestion } from "../../data/mockSurvey";
import { LikertScale } from "./LikertScale";
import { useI18n } from "../../i18n/context";

type QuestionCardProps = {
  question: SurveyQuestion;
  questionNumber: number;
  totalQuestions: number;
  selectedValue?: SurveyAnswer;
  onAnswer: (value: SurveyAnswer) => void;
  optionsOverride?: SurveyOption[];
  optionsLoading?: boolean;
  optionsDisabled?: boolean;
  optionsError?: string;
  navigation?: ReactNode;
};

function ChoiceOptions({ question, selectedValue, onAnswer, optionsOverride, optionsLoading, optionsDisabled, optionsError }: Omit<QuestionCardProps, "questionNumber" | "totalQuestions" | "navigation">) {
  const { t } = useI18n();
  const options = optionsOverride ?? question.options ?? [];
  if (question.type === "select") {
    const disabled = Boolean(optionsDisabled || optionsLoading || options.length === 0);
    return (
      <>
        <label className="survey-select-field">
          <span className="visually-hidden">{question.text}</span>
          <select aria-label={question.text} disabled={disabled} onChange={(event) => onAnswer(event.target.value)} value={typeof selectedValue === "string" ? selectedValue : ""}>
          <option disabled value="">{optionsLoading ? t("survey.loadingOptions") : question.placeholder ?? t("survey.selectOption")}</option>
            {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
        {optionsError && <p className="survey-field-error" role="alert">{optionsError}</p>}
      </>
    );
  }

  if (question.type === "multiple_choice") {
    const selected = Array.isArray(selectedValue) ? selectedValue : [];
    return (
      <fieldset className="survey-choice-list survey-choice-list--multiple">
        <legend className="visually-hidden">{question.helperText ?? t("survey.selectMultiple")}</legend>
        {options.map((option) => {
          const checked = selected.includes(option.value);
          return (
            <label className="survey-choice" key={option.value}>
              <input checked={checked} onChange={() => {
                if (option.exclusive) onAnswer(checked ? [] : [option.value]);
                else {
                  const withoutExclusive = selected.filter((value) => !options.find((item) => item.value === value)?.exclusive);
                  onAnswer(checked ? withoutExclusive.filter((value) => value !== option.value) : [...withoutExclusive, option.value]);
                }
              }} type="checkbox" value={option.value} />
              <span className="survey-choice__label">{option.label}</span>
            </label>
          );
        })}
      </fieldset>
    );
  }

  return (
    <fieldset className="survey-choice-list">
      <legend className="visually-hidden">{question.helperText ?? t("survey.selectOption")}</legend>
      {options.map((option) => <label className="survey-choice" key={option.value}>
        <input checked={selectedValue === option.value} name={`answer-${question.id}`} onChange={() => onAnswer(option.value)} type="radio" value={option.value} />
        <span className="survey-choice__label">{option.label}</span>
      </label>)}
    </fieldset>
  );
}

function NpsScale({ question, selectedValue, onAnswer }: Omit<QuestionCardProps, "questionNumber" | "totalQuestions" | "navigation">) {
  const { t } = useI18n();
  return (
    <fieldset className="nps-scale">
      <legend>{question.helperText ?? t("survey.selectNps")}</legend>
      <div className="nps-scale__options">{question.options?.map((option) => <label className="nps-option" key={option.value}>
        <input checked={selectedValue === option.value} name={`answer-${question.id}`} onChange={() => onAnswer(option.value)} type="radio" value={option.value} />
        <span>{option.score ?? option.label}</span>
      </label>)}</div>
      <div className="nps-scale__captions"><span>{question.lowLabel ?? ""}</span><span>{question.highLabel ?? ""}</span></div>
    </fieldset>
  );
}

function TextAnswer({ question, selectedValue, onAnswer }: Omit<QuestionCardProps, "questionNumber" | "totalQuestions" | "navigation">) {
  const value = typeof selectedValue === "string" ? selectedValue : "";
  const common = {
    "aria-label": question.text,
    onChange: (event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => onAnswer(event.target.value),
    placeholder: question.placeholder,
    value,
  };
  return question.type === "short_text" ? <input className="survey-text-input" {...common} /> : <textarea className="survey-textarea" rows={5} {...common} />;
}

export function QuestionCard(props: QuestionCardProps) {
  const { question, questionNumber, totalQuestions, selectedValue, onAnswer, navigation } = props;
  const { t } = useI18n();
  return (
    <section className="question-card" aria-labelledby="current-question-title">
      <p className="question-card__count">{t("survey.question", { number: questionNumber })} <span>{t("survey.of")} {totalQuestions}</span></p>
      <h1 id="current-question-title">{question.text}</h1>
      {question.helperText && <p className="question-card__helper">{question.helperText}</p>}
      <div className="question-card__response">
        {question.type === "likert" && <LikertScale questionId={question.id} options={question.options ?? []} onChange={onAnswer} selectedValue={typeof selectedValue === "string" ? selectedValue : undefined} />}
        {(question.type === "select" || question.type === "single_choice" || question.type === "multiple_choice") && <ChoiceOptions {...props} />}
        {question.type === "nps" && <NpsScale onAnswer={onAnswer} question={question} selectedValue={selectedValue} />}
        {(question.type === "textarea" || question.type === "short_text") && <TextAnswer onAnswer={onAnswer} question={question} selectedValue={selectedValue} />}
      </div>
      {navigation}
    </section>
  );
}
