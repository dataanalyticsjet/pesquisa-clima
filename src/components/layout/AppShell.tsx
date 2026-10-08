import { useEffect } from "react";
import { useRouterState } from "@tanstack/react-router";
import { installPrivacyUiDeterrents } from "../../lib/privacy-ui-deterrents";
import { SurveyDemoProvider } from "../survey/SurveyDemoContext";
import { LanguageProvider } from "../../i18n/context";
import { AppHeader } from "./AppHeader";

type AppShellProps = {
  children: React.ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  useEffect(() => installPrivacyUiDeterrents(), []);

  const isLoginRoute = useRouterState({
    select: (state) => state.location.pathname === "/login",
  });

  return (
    <LanguageProvider>
      <SurveyDemoProvider>
        <>
          {!isLoginRoute && <AppHeader />}
          <main className={isLoginRoute ? "login-main" : "app-main"}>
            {isLoginRoute ? children : <div className="app-main__inner">{children}</div>}
          </main>
        </>
      </SurveyDemoProvider>
    </LanguageProvider>
  );
}
