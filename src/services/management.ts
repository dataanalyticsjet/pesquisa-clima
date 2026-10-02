import { apiRequest } from "../lib/api";

export type ManagementPillar = {
  code: string;
  title: string;
  question_count: number;
  respondent_count: number;
  analytics_available: boolean;
  index: number | null;
};

export type ManagementPillarsResponse = {
  survey_code: string;
  survey_status: string;
  min_group_size: number;
  pillars: ManagementPillar[];
};

export function getManagementPillars(surveyCode: string) {
  return apiRequest<ManagementPillarsResponse>(
    `/api/management/surveys/${encodeURIComponent(surveyCode)}/pillars`,
  );
}
