import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  return (
    <section className="welcome-panel" aria-labelledby="welcome-title">
      <p className="welcome-panel__context">Ambiente Organizacional</p>
      <h1 className="welcome-panel__title" id="welcome-title">
        Pesquisa de Clima
      </h1>
      <p className="welcome-panel__description">Plataforma em desenvolvimento</p>
      <p className="welcome-panel__institutional-copy">
        Um ambiente para ouvir, entender e acompanhar a experiência dos nossos colaboradores.
      </p>
    </section>
  );
}