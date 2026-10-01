import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { mockManagement, type ManagementFilters } from "../../data/mockManagement";

type ContextValue = { filters: ManagementFilters; setFilter: (key: keyof ManagementFilters, value: string) => void };
const emptyFilters: ManagementFilters = { regional: "", area: "", base: "", cnpj: "" };
const ManagementFilterContext = createContext<ContextValue | null>(null);

export function ManagementFilterProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState(emptyFilters);
  const value = useMemo(() => ({
    filters,
    setFilter: (key: keyof ManagementFilters, nextValue: string) =>
      setFilters((current) => ({ ...current, [key]: nextValue })),
  }), [filters]);
  return <ManagementFilterContext.Provider value={value}>{children}</ManagementFilterContext.Provider>;
}

export function useManagementFilters() {
  const value = useContext(ManagementFilterContext);
  if (!value) throw new Error("Management filters must be used inside ManagementFilterProvider.");
  return value;
}

export function ManagementFiltersBar() {
  const { filters, setFilter } = useManagementFilters();
  const matchingBases = mockManagement.bases.filter((base) =>
    (!filters.regional || base.regional === filters.regional)
    && (!filters.area || base.area === filters.area),
  );
  const cnpjs = matchingBases.filter((base) => !filters.base || base.id === filters.base);

  return (
    <section className="management-filters" aria-label="Filtros dos resultados demonstrativos">
      <div className="management-filters__heading">
        <div><p className="management-eyebrow">RECORTES DEMONSTRATIVOS</p><h2>Filtrar resultados</h2></div>
        <button className="management-filter-reset" type="button" onClick={() => {
          setFilter("regional", ""); setFilter("area", ""); setFilter("base", ""); setFilter("cnpj", "");
        }}>Limpar filtros</button>
      </div>
      <div className="management-filter-grid">
        <label><span>Regional</span><select value={filters.regional} onChange={(event) => {
          setFilter("regional", event.target.value); setFilter("base", ""); setFilter("cnpj", "");
        }}><option value="">Todas as regionais</option>{mockManagement.regionals.map((regional) => <option key={regional}>{regional}</option>)}</select></label>
        <label><span>Área</span><select value={filters.area} onChange={(event) => {
          setFilter("area", event.target.value); setFilter("base", ""); setFilter("cnpj", "");
        }}><option value="">Todas as áreas</option>{mockManagement.areas.map((area) => <option key={area}>{area}</option>)}</select></label>
        <label><span>Base / Unidade</span><select value={filters.base} onChange={(event) => {
          setFilter("base", event.target.value); setFilter("cnpj", "");
        }}><option value="">Todas as bases/unidades</option>{matchingBases.map((base) => <option key={base.id} value={base.id}>{base.name}</option>)}</select></label>
        <label><span>CNPJ / Unidade</span><select value={filters.cnpj} onChange={(event) => setFilter("cnpj", event.target.value)}><option value="">Todos os CNPJs/unidades</option>{cnpjs.map((base) => <option key={base.cnpj} value={base.cnpj}>{base.cnpj} · {base.name}</option>)}</select></label>
      </div>
      <p className="management-filters__note">Área e unidades são dados fictícios desta demonstração. Resultados exibidos somente de forma consolidada.</p>
    </section>
  );
}
