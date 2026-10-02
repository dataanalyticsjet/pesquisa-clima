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

export type ManagementOverviewResponse = {
  survey_code: string;
  survey_status: string;
  min_group_size: number;
  completed_participations: number;
  anonymous_response_count: number;
  respondent_count: number;
  analytics_available: boolean;
  nps: number | null;
  invited_count: number | null;
  adherence_percent: number | null;
  invited_population_source_configured: boolean;
};

export type ManagementAttentionQuestion = {
  question_code: string;
  question_text: string;
  analytics_available: boolean;
  attention_rate: number | null;
  respondent_count: number | null;
};

export type ManagementAttentionSC = {
  sc_code: string;
  sc_name: string;
  display_name: string;
  attention_rate: number | null;
  analytics_available: boolean;
  respondent_count: number | null;
  questions: ManagementAttentionQuestion[];
};

export type ManagementAttentionRegional = {
  regional_code: string;
  attention_rate: number | null;
  analytics_available: boolean;
  respondent_count: number | null;
  questions: ManagementAttentionQuestion[];
  scs: ManagementAttentionSC[];
};

export type ManagementAttentionResponse = {
  survey_code: string;
  survey_status: string;
  min_group_size: number;
  regionals: ManagementAttentionRegional[];
};

export function getManagementPillars(surveyCode: string) {
  return apiRequest<ManagementPillarsResponse>(
    `/api/management/surveys/${encodeURIComponent(surveyCode)}/pillars`,
  );
}

export function getManagementOverview(surveyCode: string) {
  return apiRequest<ManagementOverviewResponse>(
    `/api/management/surveys/${encodeURIComponent(surveyCode)}/overview`,
  );
}

export function getManagementAttention(surveyCode: string) {
  return apiRequest<ManagementAttentionResponse>(
    `/api/management/surveys/${encodeURIComponent(surveyCode)}/attention`,
  );
}
