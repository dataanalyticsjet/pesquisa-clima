import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ApiError } from "../../lib/api";
import { canAccessManagement } from "../../lib/roleNavigation";
import { getCurrentUser, logout, type AuthUser } from "../../services/auth";
import { useSurveyDemo } from "../survey/SurveyDemoContext";
import { LanguageSelector } from "./LanguageSelector";
import { useI18n } from "../../i18n/context";

export function AppHeader() {
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const { resetAnswers } = useSurveyDemo();
  const { t } = useI18n();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState(false);

  useEffect(() => {
    let active = true;
    getCurrentUser()
      .then(({ user: currentUser }) => {
        if (active) setUser(currentUser);
      })
      .catch(() => {
        if (active) setUser(null);
      });
    return () => {
      active = false;
    };
  }, [pathname]);

  async function handleLogout() {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    setLogoutError(false);
    try {
      await logout();
      resetAnswers();
      await navigate({ to: "/login", replace: true });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        resetAnswers();
        await navigate({ to: "/login", replace: true });
        return;
      }
      setLogoutError(true);
    } finally {
      setIsLoggingOut(false);
    }
  }

  return (
    <header className="app-header">
      <div className="app-header__inner">
        <Link className="app-header__home" to="/" aria-label={t("home.open")}>
          <img className="app-header__logo" src="/jt-express-logo.png" alt="J&T Express" />
          <span className="app-header__title">Pesquisa de Clima</span>
        </Link>
        <div className="app-header__actions">
          <LanguageSelector />
          {user && canAccessManagement(user.roles) && (pathname.startsWith("/management")
            ? <Link className="app-header__management" to="/home">{t("nav.respond")}</Link>
            : <Link className="app-header__management" to="/management">{t("nav.management")}</Link>)}
          {user && (
            <button
              className="app-header__logout"
              type="button"
              onClick={handleLogout}
              disabled={isLoggingOut}
              aria-label={t("nav.logoutAria")}
            >
              <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
                <path
                  d="M10 5H6.5A1.5 1.5 0 0 0 5 6.5v11A1.5 1.5 0 0 0 6.5 19H10m4-3 4-4-4-4m4 4H9"
                  fill="none"
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="1.8"
                />
              </svg>
              <span>{isLoggingOut ? t("nav.loggingOut") : t("nav.logout")}</span>
            </button>
          )}
        </div>
      </div>
      {logoutError && <p className="app-header__error" role="alert">{t("nav.logoutError")}</p>}
    </header>
  );
}
