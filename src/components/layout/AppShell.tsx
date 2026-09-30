import { AppHeader } from "./AppHeader";

type AppShellProps = {
  children: React.ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <>
      <AppHeader />
      <main className="app-main">
        <div className="app-main__inner">{children}</div>
      </main>
    </>
  );
}
