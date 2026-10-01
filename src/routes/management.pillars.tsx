import { createFileRoute } from "@tanstack/react-router";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { ManagementPillarExplorer } from "../components/management/ManagementAnalysis";
import { PillarScoreCard } from "../components/management/PillarScoreCard";
import { mockManagement } from "../data/mockManagement";

export const Route = createFileRoute("/management/pillars")({ component: ManagementPillars });

function ManagementPillars() {
  return (
    <ManagementLayout>
      <ManagementPageTitle title="Resultados por pilar" description="Explore os índices, a distribuição das avaliações e a evolução simulada de cada tema." />
      <ManagementPillarExplorer />
      <div className="pillar-score-grid" aria-label="Os dez pilares oficiais">
        {mockManagement.pillars.map((pillar) => <PillarScoreCard key={pillar.id} pillar={pillar} />)}
      </div>
      <p className="management-demo-note">Resultados e séries históricas fictícios para demonstração.</p>
    </ManagementLayout>
  );
}
