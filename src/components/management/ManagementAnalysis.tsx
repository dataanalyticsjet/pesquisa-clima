import { useState } from "react";
import { averageScore, filterManagementPriorities, filterManagementSegments, isManagementSegmentProtected, mockManagement, type ManagementFilters, type ManagementPillar } from "../../data/mockManagement";
import { useManagementFilters } from "./ManagementFilters";
import { PillarScoreCard } from "./PillarScoreCard";

function visibleSegments(filters: ManagementFilters) {
  return filterManagementSegments(filters).filter((segment) => !segment.protected);
}

function PrivacyMessage() {
  return (
    <div className="management-protected-state" role="status">
      <strong>Dados indisponíveis para preservar a confidencialidade.</strong>
      <span>Resultados exibidos somente de forma consolidada. Nenhuma resposta individual é disponibilizada.</span>
    </div>
  );
}

function Heatmap({ filters }: { filters: ManagementFilters }) {
  const byArea = Boolean(filters.regional);
  const columns = byArea
    ? mockManagement.areas.filter((area) => !filters.area || area === filters.area)
    : mockManagement.regionals.filter((regional) => !filters.regional || regional === filters.regional);
  const segments = visibleSegments(filters);

  if (isManagementSegmentProtected(filters) || segments.length === 0) return <PrivacyMessage />;

  return (
    <div className="management-matrix-scroll" role="region" aria-label="Matriz de resultados com rolagem horizontal" tabIndex={0}>
      <table className="management-matrix">
        <thead><tr><th scope="col">Pilar</th>{columns.map((column) => <th scope="col" key={column}>{column}</th>)}</tr></thead>
        <tbody>{mockManagement.pillars.map((pillar) => (
          <tr key={pillar.id}>
            <th scope="row">{pillar.name}</th>
            {columns.map((column) => {
              const values = segments.filter((segment) =>
                byArea ? segment.area === column : segment.regional === column,
              ).map((segment) => segment.pillarScores[pillar.id]).filter((score): score is number => typeof score === "number");
              const score = averageScore(values);
              return <td key={column}>{score === null ? <span aria-label="Sem dados">—</span> : <span className="management-heat-cell" title={pillar.name + " · " + column + ": " + score} data-level={score < 55 ? "low" : score < 70 ? "mid" : "high"}>{score}</span>}</td>;
            })}
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function PriorityList({ filters }: { filters: ManagementFilters }) {
  const priorities = filterManagementPriorities(filters);
  if (isManagementSegmentProtected(filters)) return <PrivacyMessage />;
  if (!priorities.length) return <p className="management-demo-note">Nenhuma prioridade mockada corresponde a este recorte.</p>;

  return (
    <div className="management-priority-list">
      {priorities.map((item, index) => {
        const pillar = mockManagement.pillars.find((candidate) => candidate.id === item.pillarId);
        if (!pillar) return null;
        return (
          <article className="management-priority" key={item.regional + item.area + item.pillarId}>
            <span className="management-priority__rank">{String(index + 1).padStart(2, "0")}</span>
            <div><strong>{item.regional} · {item.area}</strong><span>{pillar.name}</span></div>
            <b aria-label={"Índice " + item.score + " de 100"}>{item.score}<small>/100</small></b>
          </article>
        );
      })}
    </div>
  );
}

export function ManagementOverviewAnalysis() {
  const { filters } = useManagementFilters();
  return (
    <>
      <section className="management-section" aria-labelledby="regional-area-analysis">
        <div className="management-section__heading">
          <div><p className="management-eyebrow">ANÁLISE CRUZADA</p><h2 id="regional-area-analysis">Análise por Regional e Área</h2></div>
        </div>
        <p className="management-analysis-caption">{filters.regional ? "Resultado por pilar e área na regional " + filters.regional : "Comparativo por regional; selecione uma regional para detalhar por área."}</p>
        <Heatmap filters={filters} />
      </section>
      <section className="management-section" aria-labelledby="management-priorities-title">
        <div className="management-section__heading">
          <div><p className="management-eyebrow">ONDE ATUAR</p><h2 id="management-priorities-title">Prioridades de atuação</h2></div>
        </div>
        <PriorityList filters={filters} />
        <p className="management-demo-note">Prioridades demonstrativas mockadas para orientar a discussão de atuação.</p>
      </section>
    </>
  );
}

export function ManagementNpsSummary() {
  const nps = mockManagement.nps;
  return (
    <section className="management-nps-card" aria-labelledby="management-nps-title">
      <div className="management-nps-card__score"><p className="management-eyebrow">RECOMENDAÇÃO</p><h2 id="management-nps-title">NPS</h2><strong>+{nps.score}</strong><span>pontos NPS · escala de -100 a +100</span></div>
      <div className="management-nps-card__distribution" aria-label="Distribuição NPS">
        <div><span>Promotores</span><strong>{nps.promoters}%</strong><i><b style={{ width: nps.promoters + "%" }} /></i></div>
        <div><span>Neutros</span><strong>{nps.neutral}%</strong><i><b style={{ width: nps.neutral + "%" }} /></i></div>
        <div><span>Detratores</span><strong>{nps.detractors}%</strong><i><b style={{ width: nps.detractors + "%" }} /></i></div>
      </div>
      <p className="management-demo-note">NPS demonstrativo separado do score dos pilares.</p>
    </section>
  );
}

function distributionFor(score: number) {
  const neutral = Math.max(12, Math.min(28, Math.round((100 - score) * 0.35)));
  const negative = Math.max(8, Math.min(60, 100 - score));
  return { positive: 100 - neutral - negative, neutral, negative };
}

function adjustedPillar(pillar: ManagementPillar, filters: ManagementFilters) {
  const segments = visibleSegments(filters);
  const hasFilters = Object.values(filters).some(Boolean);
  const score = hasFilters
    ? averageScore(segments.map((segment) => segment.pillarScores[pillar.id]).filter((value): value is number => typeof value === "number"))
    : pillar.score;
  if (score === null) return pillar;
  const shift = score - pillar.score;
  return {
    ...pillar,
    score,
    distribution: hasFilters ? distributionFor(score) : pillar.distribution,
    questions: pillar.questions.map((question) => ({ ...question, score: Math.max(0, Math.min(100, question.score + shift)) })),
  };
}

export function ManagementPillarExplorer() {
  const { filters } = useManagementFilters();
  const [selectedId, setSelectedId] = useState(mockManagement.pillars[0]?.id ?? "");
  const selected = mockManagement.pillars.find((pillar) => pillar.id === selectedId) ?? mockManagement.pillars[0];
  const pillar = adjustedPillar(selected, filters);
  const regionalScores = mockManagement.regionals.map((regional) => {
    const matches = visibleSegments({ ...filters, regional });
    return { label: regional, score: averageScore(matches.map((segment) => segment.pillarScores[pillar.id]).filter((score): score is number => typeof score === "number")) };
  });
  const areaScores = mockManagement.areas.map((area) => {
    const matches = visibleSegments({ ...filters, area });
    return { label: area, score: averageScore(matches.map((segment) => segment.pillarScores[pillar.id]).filter((score): score is number => typeof score === "number")) };
  });

  return (
    <section className="management-section management-pillar-explorer" aria-labelledby="pillar-explorer-title">
      <div className="management-section__heading">
        <div><p className="management-eyebrow">DETALHE POR PILAR</p><h2 id="pillar-explorer-title">Explorar um pilar</h2></div>
        <label className="management-dimension-select"><span>Pilar</span><select value={pillar.id} onChange={(event) => setSelectedId(event.target.value)}>{mockManagement.pillars.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      </div>
      {isManagementSegmentProtected(filters) ? <PrivacyMessage /> : (
        <div className="management-pillar-detail-grid">
          <PillarScoreCard pillar={pillar} detailed />
          <div className="management-dimension-breakdowns">
            <div><h3>Score por Regional</h3><ul>{regionalScores.map((item) => <li key={item.label}><span>{item.label}</span><b>{item.score ?? "—"}</b></li>)}</ul></div>
            <div><h3>Score por Área</h3><ul>{areaScores.map((item) => <li key={item.label}><span>{item.label}</span><b>{item.score ?? "—"}</b></li>)}</ul></div>
          </div>
        </div>
      )}
      <p className="management-demo-note">Scores e distribuições demonstrativos. Os textos das perguntas vêm do questionário oficial.</p>
    </section>
  );
}
