import { mockSurvey } from "../../data/mockSurvey";

type LikertScaleProps = {
  questionId: string;
  selectedValue?: number;
  onChange: (value: number) => void;
};

export function LikertScale({ questionId, selectedValue, onChange }: LikertScaleProps) {
  const firstOption = mockSurvey.scale[0];
  const lastOption = mockSurvey.scale[mockSurvey.scale.length - 1];

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
              <span className="visually-hidden">{option.label}</span>
            </span>
          </label>
        ))}
      </div>
      <div className="likert-scale__captions" aria-hidden="true">
        <span>{firstOption.label}</span>
        <span>{lastOption.label}</span>
      </div>
    </fieldset>
  );
}
