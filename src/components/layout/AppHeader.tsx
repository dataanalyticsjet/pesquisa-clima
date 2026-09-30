import { LanguageSelector } from "./LanguageSelector";

export function AppHeader() {
  return (
    <header className="app-header">
      <div className="app-header__inner">
        <div className="app-header__identity" aria-label="J&T Express Pesquisa de Clima">
          <span className="app-header__company">J&amp;T EXPRESS</span>
          <span className="app-header__product">Pesquisa de Clima</span>
        </div>
        <LanguageSelector />
      </div>
    </header>
  );
}