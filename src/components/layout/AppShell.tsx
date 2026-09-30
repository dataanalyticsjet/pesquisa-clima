import { useRouterState } from "@tanstack/react-router";
import { AppHeader } from "./AppHeader";

type AppShellProps = {
  children: React.ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const isLoginRoute = useRouterState({
    select: (state) => state.location.pathname === "/login",
  });

  return (
    <>
      {!isLoginRoute && <AppHeader />}
      <main className={isLoginRoute ? "login-main" : "app-main"}>
        {isLoginRoute ? children : <div className="app-main__inner">{children}</div>}
      </main>
    </>
  );
}