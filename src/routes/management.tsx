import { Outlet, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/management")({ component: ManagementShell });

function ManagementShell() {
  return <Outlet />;
}
