import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  return (
    <main>
      <h1>Pesquisa de Clima</h1>
      <p>Plataforma em desenvolvimento</p>
    </main>
  )
}