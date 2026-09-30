import { useRouterState } from "@tanstack/react-router";
import { SurveyDemoProvider } from "../survey/SurveyDemoContext";
import { AppHeader } from "./AppHeader";

type AppShellProps = {
  children: React.ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const isLoginRoute = useRouterState({
    select: (state) => state.location.pathname === "/login",
  });

  return (
    <SurveyDemoProvider>
      <>
        {!isLoginRoute && <AppHeader />}
        <main className={isLoginRoute ? "login-main" : "app-main"}>
          {isLoginRoute ? children : <div className="app-main__inner">{children}</div>}
        </main>
      </>
    </SurveyDemoProvider>
  );
}
