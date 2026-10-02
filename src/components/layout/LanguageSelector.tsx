type Language = "PT" | "中文";

type LanguageSelectorProps = {
  className?: string;
};

const languages: Language[] = ["PT", "中文"];

export function LanguageSelector({ className = "" }: LanguageSelectorProps) {
  const classes = ["app-header__languages", className].filter(Boolean).join(" ");

  return (
    <div className={classes} role="group" aria-label="Idiomas disponíveis">
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
  );
}
