import { createFileRoute } from "@tanstack/react-router";
import { useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { ManagementPillarApiCard } from "../components/management/ManagementPillarApiCard";
import { ApiError } from "../lib/api";
import { getManagementPillars, type ManagementPillarsResponse } from "../services/management";

export const Route = createFileRoute("/management/pillars")({ component: ManagementPillars });

const surveyCode = "CLIMATE_2026";

function ManagementPillars() {
  const navigate = useNavigate();
  const [data, setData] = useState<ManagementPillarsResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getManagementPillars(surveyCode)
      .then((result) => { if (active) setData(result); })
      .catch((reason: unknown) => {
        if (!active) return;
        if (reason instanceof ApiError && reason.status === 401) {
          void navigate({ to: "/login", replace: true });
          return;
        }
        if (reason instanceof ApiError && reason.status === 403) {
          setError("Seu perfil não tem autorização para acessar os resultados de gestão.");
        } else if (reason instanceof ApiError && reason.status === 404) {
          setError("A pesquisa solicitada não foi encontrada.");
        } else if (reason instanceof ApiError && reason.status === 503) {
          setError("Os resultados dos pilares estão temporariamente indisponíveis. Tente novamente mais tarde.");
        } else {
          setError("Não foi possível carregar os resultados. Verifique sua conexão e tente novamente.");
        }
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [navigate]);

  return (
    <ManagementLayout>
      <ManagementPageTitle title="Resultados por pilar" description="Índices consolidados dos pilares da Pesquisa de Clima, respeitando o mínimo de respostas para divulgação." />
      {loading && (
        <div className="management-pillars-state" role="status" aria-live="polite">
          <span className="management-pillars-state__spinner" aria-hidden="true" />
          <span>Carregando resultados dos pilares…</span>
        </div>
      )}
      {!loading && error && <p className="management-pillars-state management-pillars-state--error" role="alert">{error}</p>}
      {!loading && data && (
        <div className="pillar-score-grid" aria-label="Resultados dos dez pilares">
          {data.pillars.map((pillar) => (
            <ManagementPillarApiCard
              key={pillar.code}
              pillar={pillar}
              minGroupSize={data.min_group_size}
            />
          ))}
        </div>
      )}
    </ManagementLayout>
  );
}
