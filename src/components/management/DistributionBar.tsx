import type { ManagementDistribution } from "../../data/mockManagement";

const labels: { key: keyof ManagementDistribution; label: string }[] = [
  { key: "positive", label: "Positivas" },
  { key: "neutral", label: "Neutras" },
  { key: "negative", label: "Negativas" },
];

export function DistributionBar({ distribution }: { distribution: ManagementDistribution }) {
  return (
    <div className="distribution" role="group" aria-label="Distribuição das avaliações">
      <div className="distribution__bar" aria-hidden="true">
        <span className="distribution__segment distribution__segment--positive" style={{ width: `${distribution.positive}%` }} />
        <span className="distribution__segment distribution__segment--neutral" style={{ width: `${distribution.neutral}%` }} />
        <span className="distribution__segment distribution__segment--negative" style={{ width: `${distribution.negative}%` }} />
      </div>
      <ul className="distribution__legend">
        {labels.map(({ key, label }) => (
          <li key={key}>
            <span className={`distribution__dot distribution__dot--${key}`} aria-hidden="true" />
            <span>{label}</span>
            <strong>{distribution[key]}%</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}
