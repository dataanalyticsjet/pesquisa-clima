type Language = "PT" | "中文" | "EN";

const languages: Language[] = ["PT", "中文", "EN"];

export function AppHeader() {
  return (
    <header className="app-header">
      <div className="app-header__inner">
        <div className="app-header__identity" aria-label="J&T Express Pesquisa de Clima">
          <span className="app-header__company">J&amp;T EXPRESS</span>
          <span className="app-header__product">Pesquisa de Clima</span>
        </div>
        <div className="app-header__languages" aria-label="Idiomas disponíveis">
          {languages.map((language, index) => (
            <span className="app-header__language-item" key={language}>
              {index > 0 && (
                <span className="app-header__language-separator" aria-hidden="true">
                  |
                </span>
              )}
              <span
                className={language === "PT" ? "app-header__language-active" : undefined}
                aria-current={language === "PT" ? "true" : undefined}
              >
                {language}
              </span>
            </span>
          ))}
        </div>
      </div>
    </header>
  );
}