type Point = { year: number; score: number };

export function TrendChart({ title, values, compact = false }: { title: string; values: Point[]; compact?: boolean }) {
  const width = 640;
  const height = compact ? 160 : 220;
  const paddingX = 42;
  const paddingY = 24;
  const scores = values.map(({ score }) => score);
  const min = Math.max(0, Math.min(...scores) - 10);
  const max = Math.min(100, Math.max(...scores) + 10);
  const points = values.map((point, index) => ({
    ...point,
    x: paddingX + (index * (width - paddingX * 2)) / Math.max(1, values.length - 1),
    y: height - paddingY - ((point.score - min) / Math.max(1, max - min)) * (height - paddingY * 2),
  }));
  const path = points.map(({ x, y }, index) => `${index === 0 ? "M" : "L"} ${x} ${y}`).join(" ");

  return (
    <figure className={`trend-chart${compact ? " trend-chart--compact" : ""}`}>
      <figcaption>{title}</figcaption>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${title}: ${values.map(({ year, score }) => `${year}, índice ${score}`).join("; ")}`}>
        <line className="trend-chart__axis" x1={paddingX} y1={height - paddingY} x2={width - paddingX} y2={height - paddingY} />
        <path className="trend-chart__line" d={path} />
        {points.map(({ x, y, year, score }) => (
          <g key={year}>
            <circle className="trend-chart__point" cx={x} cy={y} r="5" />
            <text className="trend-chart__value" x={x} y={y - 13} textAnchor="middle">{score}</text>
            <text className="trend-chart__year" x={x} y={height - 5} textAnchor="middle">{year}</text>
          </g>
        ))}
      </svg>
    </figure>
  );
}
