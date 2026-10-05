import { Outlet, createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ApiError } from "../lib/api";
import { canAccessManagement } from "../lib/roleNavigation";
import { getCurrentUser } from "../services/auth";
import { useI18n } from "../i18n/context";

export const Route = createFileRoute("/management")({ component: ManagementShell });

function ManagementShell() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const [access, setAccess] = useState<"checking" | "allowed" | "unavailable">("checking");

  useEffect(() => {
    let active = true;
    getCurrentUser().then(({ user }) => {
      if (!active) return;
      if (canAccessManagement(user.roles)) {
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
    return <p role="status" className="api-state">{t("management.validating")}</p>;
  }
  if (access === "unavailable") {
    return <p role="alert" className="api-state">{t("management.accessError")}</p>;
  }
  return <Outlet />;
}
