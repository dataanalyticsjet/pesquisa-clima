import { Outlet, createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ApiError } from "../lib/api";
import { getCurrentUser } from "../services/auth";

export const Route = createFileRoute("/management")({ component: ManagementShell });

const managementRoles = ["MANAGEMENT", "SURVEY_ADMIN", "ADMIN"];

function ManagementShell() {
  const navigate = useNavigate();
  const [access, setAccess] = useState<"checking" | "allowed" | "unavailable">("checking");

  useEffect(() => {
    let active = true;
    getCurrentUser().then(({ user }) => {
      if (!active) return;
      if (user.roles.some((role) => managementRoles.includes(role))) {
        setAccess("allowed");
      } else {
        void navigate({ to: "/home", replace: true });
      }
    }).catch((reason: unknown) => {
      if (!active) return;
      if (reason instanceof ApiError && reason.status === 401) {
        void navigate({ to: "/login", replace: true });
      } else if (reason instanceof ApiError && reason.status === 403) {
        void navigate({ to: "/home", replace: true });
      } else {
        setAccess("unavailable");
      }
    });
    return () => { active = false; };
  }, [navigate]);

  if (access === "checking") {
    return <p role="status" className="api-state">Validando acesso à Gestão…</p>;
  }
  if (access === "unavailable") {
    return <p role="alert" className="api-state">Não foi possível validar seu acesso à Gestão. Verifique sua conexão e tente novamente.</p>;
  }
  return <Outlet />;
}
