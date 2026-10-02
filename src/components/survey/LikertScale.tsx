import type { SurveyOption } from "../../data/mockSurvey";

type LikertScaleProps = {
  questionId: string;
  selectedValue?: string;
  options: SurveyOption[];
  onChange: (value: string) => void;
};

export function LikertScale({ questionId, selectedValue, options, onChange }: LikertScaleProps) {
  return (
    <fieldset className="likert-scale">
      <legend>Selecione seu nível de concordância</legend>
      <div className="likert-scale__options" role="radiogroup">
        {options.map((option) => (
          <label className="likert-option" key={option.value}>
            <input
              checked={selectedValue === option.value}
              name={`answer-${questionId}`}
              onChange={() => onChange(option.value)}
              type="radio"
              value={option.value}
            />
            <span className="likert-option__tile">
              <strong>{option.score ?? option.label}</strong>
              <span>{option.score ?? option.label} — {option.label}</span>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
