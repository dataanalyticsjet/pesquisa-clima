import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { getCurrentUser } from "../services/auth";
import { getAuthenticatedLandingPath } from "../lib/roleNavigation";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const navigate = useNavigate();
  useEffect(() => {
    const authError = new URLSearchParams(window.location.search).get("auth_error");
    if (authError) {
      window.location.replace(`/login?auth_error=${encodeURIComponent(authError)}`);
      return;
    }
    let active = true;
    getCurrentUser()
      .then(({ user }) => { if (active) void navigate({ to: getAuthenticatedLandingPath(user.roles), replace: true }); })
      .catch(() => { if (active) void navigate({ to: "/login", replace: true }); });
    return () => { active = false; };
  }, [navigate]);

  return (
    <p role="status" className="api-state">Abrindo a página inicial…</p>
  );
}
