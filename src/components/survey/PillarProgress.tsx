import { mockSurvey } from "../../data/mockSurvey";

type PillarProgressProps = {
  currentPillarIndex: number | null;
  answers: Record<string, number>;
};

export function PillarProgress({ currentPillarIndex, answers }: PillarProgressProps) {
  return (
    <ol className="pillar-progress" aria-label="Etapas por pilar">
      {mockSurvey.pillars.map((pillar, index) => {
        const isComplete = pillar.questions.every((question) => answers[question.id] !== undefined);
        const isCurrent = currentPillarIndex === index;
        const state = isCurrent ? "current" : isComplete ? "complete" : "pending";

        return (
          <li className={`pillar-progress__item pillar-progress__item--${state}`} key={pillar.id}>
            <span className="pillar-progress__marker" aria-hidden="true">
              {isComplete && !isCurrent ? "✓" : index + 1}
            </span>
            <span className="pillar-progress__name">{pillar.name}</span>
          </li>
        );
      })}
    </ol>
  );
}
