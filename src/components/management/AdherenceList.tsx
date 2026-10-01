export function AdherenceList({ regions }: { regions: { region: string; adherence: number }[] }) {
  return (
    <ul className="adherence-list">
      {regions.map(({ region, adherence }) => (
        <li className="adherence-row" key={region}>
          <span className="adherence-row__region">{region}</span>
          <div className="adherence-row__track" role="progressbar" aria-label={`Adesão ${region}`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={adherence}>
            <span style={{ width: `${adherence}%` }} />
          </div>
          <strong>{adherence}%</strong>
        </li>
      ))}
    </ul>
  );
}
