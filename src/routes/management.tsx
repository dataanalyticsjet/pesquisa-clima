import { Outlet, createFileRoute } from "@tanstack/react-router";
import { ManagementFilterProvider } from "../components/management/ManagementFilters";

export const Route = createFileRoute("/management")({ component: ManagementShell });

function ManagementShell() {
  return <ManagementFilterProvider><Outlet /></ManagementFilterProvider>;
}
