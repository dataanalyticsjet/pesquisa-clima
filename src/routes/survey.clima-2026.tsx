import { createFileRoute } from "@tanstack/react-router";
import { SurveyFlow } from "../components/survey/SurveyFlow";

export const Route = createFileRoute("/survey/clima-2026")({
  component: SurveyFlow,
});
