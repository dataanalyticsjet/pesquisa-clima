type LanguageSelectorProps = {
  className?: string;
};

import { useI18n } from "../../i18n/context";

export function LanguageSelector({ className = "" }: LanguageSelectorProps) {
  const { locale, setLocale, t } = useI18n();
  const classes = ["app-header__languages", className].filter(Boolean).join(" ");

  return (
    <div className={classes} role="group" aria-label={t("language.label")}>
      <button className={`app-header__language-button${locale === "pt" ? " app-header__language-active" : ""}`} type="button" aria-pressed={locale === "pt"} onClick={() => setLocale("pt")}>
        PT
      </button>
      <span className="app-header__language-separator" aria-hidden="true">|</span>
      <button className={`app-header__language-button${locale === "zh" ? " app-header__language-active" : ""}`} type="button" aria-pressed={locale === "zh"} onClick={() => setLocale("zh")}>
        中文
      </button>
    </div>
  );
}
