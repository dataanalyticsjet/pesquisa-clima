import type { SurveyAnswer, SurveyQuestion, SurveyQuestionType, SurveySection } from "../data/mockSurvey";
import { apiRequest } from "../lib/api";

type ApiOption = { code: string; label: string; position: number; score_value: number | null; is_exclusive: boolean };
type ApiQuestion = {
  question_number: number; code: string; question_type: string; text: string; helper_text: string | null;
  placeholder: string | null; low_label: string | null; high_label: string | null; required: boolean;
  position: number; analysis_role: string; option_source: string; options: ApiOption[];
};
type ApiSection = { code: string; title: string; position: number; analysis_type: string; questions: ApiQuestion[] };
export type SurveyDefinition = {
  code: string; title: string; intro_text: string | null; completion_text: string | null;
  status: string; version: number; sections: SurveySection[]; questions: SurveyQuestion[];
};
export type ParticipationStatus = { survey_code: string; completed: boolean; completed_on?: string };

function adaptQuestion(question: ApiQuestion, sectionId: string): SurveyQuestion {
  const type = question.question_type.toLowerCase() as SurveyQuestionType;
  return {
    id: question.code,
    number: question.question_number,
    sectionId,
    type,
    text: question.text,
    required: question.required,
    helperText: question.helper_text ?? undefined,
    optionSource: question.option_source,
    placeholder: question.placeholder ?? undefined,
    lowLabel: question.low_label ?? undefined,
    highLabel: question.high_label ?? undefined,
    options: question.options.map((option) => ({
      value: option.code,
      label: option.label,
      exclusive: option.is_exclusive,
      score: option.score_value ?? undefined,
    })),
  } as SurveyQuestion;
}

export async function getSurveyDefinition(code: string): Promise<SurveyDefinition> {
  const data = await apiRequest<Omit<SurveyDefinition, "sections" | "questions"> & { sections: ApiSection[] }>(`/api/surveys/${encodeURIComponent(code)}`);
  const sections = [...data.sections].sort((a, b) => a.position - b.position);
  return {
    ...data,
    sections: sections.map((section) => ({ id: section.code, name: section.title })),
    questions: sections.flatMap((section) => [...section.questions].sort((a, b) => a.position - b.position).map((question) => adaptQuestion(question, section.code))),
  };
}

export function getParticipationStatus(code: string) {
  return apiRequest<ParticipationStatus>(`/api/surveys/${encodeURIComponent(code)}/participation`);
}

export type { SurveyAnswer };


export type OrganizationRegional = { code: string; label: string };
export type OrganizationServiceCenter = { code: string; name: string; display_name: string };
export type SurveySubmissionAnswer = { question_code: string; option_codes?: string[]; text_value?: string };

export function getOrganizationRegionals() {
  return apiRequest<{ regionals: OrganizationRegional[] }>("/api/organization/regionals");
}

export function getOrganizationServiceCenters(regionalCode: string) {
  return apiRequest<{ regional_code: string; service_centers: OrganizationServiceCenter[] }>(
    `/api/organization/regionals/${encodeURIComponent(regionalCode)}/scs`,
  );
}

export function submitSurveyResponses(code: string, answers: SurveySubmissionAnswer[]) {
  return apiRequest<{ submitted: true }>(`/api/surveys/${encodeURIComponent(code)}/responses`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}
