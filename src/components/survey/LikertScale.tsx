import { mockSurvey } from "../../data/mockSurvey";

type LikertScaleProps = {
  questionId: string;
  selectedValue?: number;
  onChange: (value: number) => void;
};

export function LikertScale({ questionId, selectedValue, onChange }: LikertScaleProps) {
  return (
    <fieldset className="likert-scale">
      <legend>Selecione seu nível de concordância</legend>
      <div className="likert-scale__options" role="radiogroup">
        {mockSurvey.scale.map((option) => (
          <label className="likert-option" key={option.value}>
            <input
              checked={selectedValue === option.value}
              name={`answer-${questionId}`}
              onChange={() => onChange(option.value)}
              type="radio"
              value={option.value}
            />
            <span className="likert-option__tile">
              <strong>{option.value}</strong>
              <span>{option.value} — {option.label}</span>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
