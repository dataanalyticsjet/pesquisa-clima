export function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail?: string;
}) {
  return (
    <article className="management-metric">
      <p className="management-metric__label">{label}</p>
      <p className="management-metric__value">{value}</p>
      {detail && <p className="management-metric__detail">{detail}</p>}
    </article>
  );
}
