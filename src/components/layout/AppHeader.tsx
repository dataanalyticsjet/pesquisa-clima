import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ApiError } from "../../lib/api";
import { canAccessManagement } from "../../lib/roleNavigation";
import { getCurrentUser, logout, type AuthUser } from "../../services/auth";
import { useSurveyDemo } from "../survey/SurveyDemoContext";
import { LanguageSelector } from "./LanguageSelector";

export function AppHeader() {
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const { resetAnswers } = useSurveyDemo();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState("");

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
    setLogoutError("");
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
      setLogoutError("Não foi possível encerrar a sessão. Tente novamente.");
    } finally {
      setIsLoggingOut(false);
    }
  }

  return (
    <header className="app-header">
      <div className="app-header__inner">
        <Link className="app-header__home" to="/" aria-label="Pesquisa de Clima — início">
          <img className="app-header__logo" src="/jt-express-logo.png" alt="J&T Express" />
        </Link>
        <div className="app-header__actions">
          <LanguageSelector />
          {user && canAccessManagement(user.roles) && (
            <Link className="app-header__management" to="/management">
              Gestão
            </Link>
          )}
          {user && (
            <button
              className="app-header__logout"
              type="button"
              onClick={handleLogout}
              disabled={isLoggingOut}
              aria-label="Sair da plataforma"
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
              <span>{isLoggingOut ? "Saindo…" : "Sair"}</span>
            </button>
          )}
        </div>
      </div>
      {logoutError && <p className="app-header__error" role="alert">{logoutError}</p>}
    </header>
  );
}
