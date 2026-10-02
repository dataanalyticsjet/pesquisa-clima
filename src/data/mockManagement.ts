import { mockSurvey } from "./mockSurvey";

// DEMO ONLY
// Official source of department/area will be defined before backend implementation.

export type ManagementDistribution = {
  positive: number;
  neutral: number;
  negative: number;
};

export type ManagementCategory = { label: string; value: number };

export type ManagementCategoricalAnalysis = {
  questionNumber: number;
  title: string;
  text: string;
  categories: ManagementCategory[];
};

export type ManagementQuestionResult = {
  number: number;
  text: string;
  score: number;
};

export type ManagementPillar = {
  id: string;
  name: string;
  score: number;
  distribution: ManagementDistribution;
  trend: number;
  evolution: { year: number; score: number }[];
  questions: ManagementQuestionResult[];
  categoricalAnalyses: ManagementCategoricalAnalysis[];
};

export type ManagementAttention = {
  id: string;
  pillarId: string;
  pillar: string;
  score?: number;
  criticality: "CRITICAL" | "ATTENTION" | "HEALTHY";
  reason: string;
  question: string;
  questionScore?: number;
  regional: string;
  area: string;
  base: string;
  cnpj: string;
  questionNumber: number;
};

export type ManagementFilters = { regional: string; area: string; base: string; cnpj: string };

type PillarDefinition = {
  id: string;
  name: string;
  score: number;
  distribution: ManagementDistribution;
  trend: number;
  questionNumbers: number[];
  questionScores: number[];
  categoricalAnalyses?: { questionNumber: number; title: string; categories: ManagementCategory[] }[];
};

function officialQuestion(number: number) {
  const question = mockSurvey.questions.find((item) => item.number === number);
  if (!question) throw new Error("Official survey question Q" + number + " was not found.");
  return question.text;
}

const pillarDefinitions: PillarDefinition[] = [
  { id: "condicoes", name: "Condições e Organização do Trabalho", score: 74, distribution: { positive: 66, neutral: 19, negative: 15 }, trend: 2, questionNumbers: [4, 5], questionScores: [76, 72], categoricalAnalyses: [
    { questionNumber: 6, title: "Necessidades de melhoria", categories: [
      { label: "Sistemas ou ferramentas", value: 27 }, { label: "Equipamentos", value: 22 },
      { label: "Mobiliário", value: 15 }, { label: "Espaço de trabalho", value: 13 },
      { label: "Não identifico necessidade de melhoria", value: 11 }, { label: "Outros", value: 12 },
    ] },
  ] },
  { id: "jornada", name: "Jornada de Trabalho", score: 61, distribution: { positive: 48, neutral: 20, negative: 32 }, trend: -3, questionNumbers: [7], questionScores: [61], categoricalAnalyses: [
    { questionNumber: 8, title: "Frequência de jornada estendida", categories: [
      { label: "Nunca", value: 10 }, { label: "Raramente", value: 21 }, { label: "Algumas vezes no mês", value: 25 },
      { label: "Algumas vezes na semana", value: 32 }, { label: "Quase todos os dias", value: 12 },
    ] },
    { questionNumber: 9, title: "Principais motivos", categories: [
      { label: "Volume elevado de trabalho", value: 30 }, { label: "Falta de pessoas na equipe", value: 22 },
      { label: "Prazos ou metas difíceis", value: 14 }, { label: "Necessidade da operação", value: 12 },
      { label: "Problemas em sistemas ou equipamentos", value: 8 }, { label: "Falta de organização", value: 6 },
      { label: "Dependência de outras áreas", value: 4 }, { label: "Outros motivos", value: 4 },
    ] },
    { questionNumber: 10, title: "Ações mais indicadas", categories: [
      { label: "Melhor planejamento e organização", value: 25 }, { label: "Aumento do número de pessoas", value: 22 },
      { label: "Melhor distribuição das atividades", value: 17 }, { label: "Melhoria de sistemas e ferramentas", value: 12 },
      { label: "Revisão de metas e prazos", value: 9 }, { label: "Redução de retrabalho", value: 8 },
      { label: "Outras ações", value: 7 },
    ] },
  ] },
  { id: "lideranca", name: "Liderança e Comunicação", score: 63, distribution: { positive: 51, neutral: 20, negative: 29 }, trend: -2, questionNumbers: [11, 12, 13, 14, 15], questionScores: [66, 64, 63, 61, 61] },
  { id: "ambiente", name: "Ambiente, Respeito e Segurança", score: 79, distribution: { positive: 73, neutral: 16, negative: 11 }, trend: 2, questionNumbers: [16, 17, 18, 19, 20], questionScores: [80, 79, 78, 80, 78] },
  { id: "etica", name: "Ética e Compliance", score: 76, distribution: { positive: 69, neutral: 18, negative: 13 }, trend: 1, questionNumbers: [21, 22, 23, 24], questionScores: [78, 76, 75, 75] },
  { id: "desenvolvimento", name: "Reconhecimento e Desenvolvimento", score: 54, distribution: { positive: 39, neutral: 22, negative: 39 }, trend: -4, questionNumbers: [25, 26], questionScores: [50, 58] },
  { id: "remuneracao", name: "Remuneração e Benefícios", score: 49, distribution: { positive: 34, neutral: 22, negative: 44 }, trend: -2, questionNumbers: [27, 28], questionScores: [48, 50] },
  { id: "saude", name: "Saúde, Bem-estar e Equilíbrio", score: 68, distribution: { positive: 54, neutral: 21, negative: 25 }, trend: 1, questionNumbers: [29, 30, 31], questionScores: [70, 66, 68] },
  { id: "condicoes-ambiente", name: "Ambiente e Condições de Trabalho", score: 71, distribution: { positive: 59, neutral: 22, negative: 19 }, trend: 2, questionNumbers: [32, 33, 34, 35], questionScores: [72, 70, 70, 72] },
  { id: "permanencia", name: "Permanência e Vínculo com a Empresa", score: 66, distribution: { positive: 53, neutral: 21, negative: 26 }, trend: 0, questionNumbers: [36, 37], questionScores: [68, 64], categoricalAnalyses: [
    { questionNumber: 38, title: "Fatores que podem influenciar a saída", categories: [
      { label: "Remuneração", value: 24 }, { label: "Falta de oportunidade de crescimento", value: 18 },
      { label: "Liderança/Gestão", value: 15 }, { label: "Carga ou jornada", value: 12 },
      { label: "Falta de reconhecimento", value: 11 }, { label: "Proposta melhor", value: 9 }, { label: "Outros", value: 11 },
    ] },
  ] },
];

const pillars: ManagementPillar[] = pillarDefinitions.map((definition) => ({
  ...definition,
  questions: definition.questionNumbers.map((number, index) => ({
    number,
    text: officialQuestion(number),
    score: definition.questionScores[index]!,
  })),
  categoricalAnalyses: (definition.categoricalAnalyses ?? []).map((analysis) => ({
    ...analysis,
    text: officialQuestion(analysis.questionNumber),
  })),
  evolution: [
    { year: 2024, score: Math.max(0, definition.score - definition.trend * 2) },
    { year: 2025, score: Math.max(0, definition.score - definition.trend) },
    { year: 2026, score: definition.score },
  ],
}));

const areas = ["Operações", "Transferência / SC", "SAC", "Comercial", "Financeiro", "People", "Tecnologia", "Administrativo"] as const;
const regionals = ["SPS", "SPN", "SPE", "PR", "MG"] as const;
const regionalScores: Record<string, Record<string, number>> = {
  condicoes: { SPS: 70, SPN: 78, SPE: 75, PR: 76, MG: 74 },
  jornada: { SPS: 57, SPN: 64, SPE: 66, PR: 68, MG: 64 },
  lideranca: { SPS: 56, SPN: 61, SPE: 68, PR: 72, MG: 67 },
  ambiente: { SPS: 76, SPN: 81, SPE: 83, PR: 82, MG: 80 },
  etica: { SPS: 73, SPN: 78, SPE: 79, PR: 78, MG: 76 },
  desenvolvimento: { SPS: 49, SPN: 59, SPE: 63, PR: 67, MG: 61 },
  remuneracao: { SPS: 44, SPN: 52, SPE: 55, PR: 58, MG: 56 },
  saude: { SPS: 64, SPN: 70, SPE: 72, PR: 71, MG: 69 },
  "condicoes-ambiente": { SPS: 67, SPN: 73, SPE: 74, PR: 75, MG: 72 },
  permanencia: { SPS: 63, SPN: 68, SPE: 71, PR: 70, MG: 67 },
};
const areaAdjustments: Record<(typeof areas)[number], number> = {
  Operações: -5, "Transferência / SC": -2, SAC: 2, Comercial: 1,
  Financeiro: 8, People: 12, Tecnologia: 5, Administrativo: 3,
};
const spsAreaOverrides: Record<string, Record<string, number>> = {
  condicoes: { Operações: 65, SAC: 72, "Transferência / SC": 68, Financeiro: 78, People: 81 },
  jornada: { Operações: 52, SAC: 65, "Transferência / SC": 55, Financeiro: 72, People: 77 },
  lideranca: { Operações: 51, SAC: 63, "Transferência / SC": 58, Financeiro: 72, People: 80 },
  desenvolvimento: { Operações: 44, SAC: 57, "Transferência / SC": 45, Financeiro: 66, People: 74 },
  remuneracao: { Operações: 41, SAC: 48, "Transferência / SC": 42, Financeiro: 54, People: 62 },
};

function buildSegmentScores(regional: string, area: (typeof areas)[number]) {
  const scores = Object.fromEntries(pillars.map((pillar) => {
    const base = regionalScores[pillar.id]?.[regional] ?? pillar.score;
    const overridden = regional === "SPS" ? spsAreaOverrides[pillar.id]?.[area] : undefined;
    return [pillar.id, overridden ?? Math.max(35, Math.min(90, base + areaAdjustments[area]))];
  })) as Record<string, number>;
  if (regional === "SPN" && area === "Transferência / SC") scores.lideranca = 52;
  return scores;
}
const segments = regionals.flatMap((regional, regionalIndex) => areas.map((area, areaIndex) => ({
  id: regional.toLowerCase() + "-" + (areaIndex + 1),
  regional,
  area,
  base: "DEMO-" + regional + "-" + String(areaIndex + 1).padStart(2, "0"),
  unit: "DEMO — " + area + " / " + regional,
  cnpj: "DEMO-CNPJ-" + String(regionalIndex + 1).padStart(2, "0") + "-" + String(areaIndex + 1).padStart(2, "0"),
  responseCount: 32 + ((regionalIndex * 17 + areaIndex * 11) % 130),
  protected: false,
  pillarScores: buildSegmentScores(regional, area),
})));

segments.push({
  id: "sps-sac-protected",
  regional: "SPS",
  area: "SAC",
  base: "DEMO-SPS-SAC-PRIVACIDADE",
  unit: "DEMO — Unidade em consolidação",
  cnpj: "DEMO-CNPJ-PRIVACIDADE",
  responseCount: 4,
  protected: true,
  pillarScores: buildSegmentScores("SPS", "SAC"),
});

export type ManagementSegment = (typeof segments)[number];

const attention: ManagementAttention[] = [
  { id: "attention-remuneracao", pillarId: "remuneracao", pillar: "Remuneração e Benefícios", score: 41, criticality: "CRITICAL", reason: "56% das avaliações negativas neste recorte.", question: officialQuestion(27), questionScore: 41, questionNumber: 27, regional: "SPS", area: "Operações", base: "DEMO-SPS-01", cnpj: "DEMO-CNPJ-01-01" },
  { id: "attention-desenvolvimento", pillarId: "desenvolvimento", pillar: "Reconhecimento e Desenvolvimento", score: 44, criticality: "CRITICAL", reason: "Índice abaixo da referência demonstrativa.", question: officialQuestion(25), questionScore: 44, questionNumber: 25, regional: "SPS", area: "Operações", base: "DEMO-SPS-01", cnpj: "DEMO-CNPJ-01-01" },
  { id: "attention-lideranca", pillarId: "lideranca", pillar: "Liderança e Comunicação", score: 52, criticality: "ATTENTION", reason: "Recorte regional com oportunidade de melhoria.", question: officialQuestion(15), questionScore: 52, questionNumber: 15, regional: "SPN", area: "Transferência / SC", base: "DEMO-SPN-02", cnpj: "DEMO-CNPJ-02-02" },
  { id: "attention-jornada", pillarId: "jornada", pillar: "Jornada de Trabalho", criticality: "ATTENTION", reason: "12%: Quase todos os dias. Principal motivo (Q9): volume elevado de trabalho.", question: officialQuestion(9), questionNumber: 9, regional: "SPS", area: "Operações", base: "DEMO-SPS-01", cnpj: "DEMO-CNPJ-01-01" },
];

const priorityItems = [
  { regional: "SPS", area: "Operações", pillarId: "remuneracao", score: 41, base: "DEMO-SPS-01", cnpj: "DEMO-CNPJ-01-01" },
  { regional: "SPS", area: "Transferência / SC", pillarId: "remuneracao", score: 42, base: "DEMO-SPS-02", cnpj: "DEMO-CNPJ-01-02" },
  { regional: "SPS", area: "Operações", pillarId: "desenvolvimento", score: 44, base: "DEMO-SPS-01", cnpj: "DEMO-CNPJ-01-01" },
  { regional: "SPS", area: "Transferência / SC", pillarId: "desenvolvimento", score: 45, base: "DEMO-SPS-02", cnpj: "DEMO-CNPJ-01-02" },
  { regional: "SPN", area: "Transferência / SC", pillarId: "lideranca", score: 52, base: "DEMO-SPN-02", cnpj: "DEMO-CNPJ-02-02" },
] as const;

export const mockManagement = {
  survey: {
    title: mockSurvey.title,
    status: "ACTIVE" as const,
    invited: 5842,
    responses: 4291,
    adherence: 73.45,
    overallScore: 66,
    attentionCount: attention.length,
  },
  overallEvolution: [{ year: 2024, score: 68 }, { year: 2025, score: 67 }, { year: 2026, score: 66 }],
  pillars,
  regionals: [...regionals],
  areas: [...areas],
  bases: segments.map(({ base, unit, cnpj, regional, area, protected: isProtected }) => ({
    id: base, name: unit, cnpj, regional, area, protected: isProtected,
  })),
  segments,
  attention,
  priorityItems,
  regionalAdherence: [
    { region: "SPS", adherence: 82 }, { region: "SPE", adherence: 79 },
    { region: "PR", adherence: 77 }, { region: "MG", adherence: 74 },
    { region: "SPN", adherence: 71 },
  ],
  nps: { score: 38, promoters: 58, neutral: 22, detractors: 20 },
  voice: {
    answers: [
      { questionNumber: 40, text: officialQuestion(40), comments: [
        "Melhor alinhamento das prioridades no início do turno.",
        "Distribuir as atividades considerando o volume de cada equipe.",
        "Planejar as demandas com mais antecedência.",
      ] },
      { questionNumber: 41, text: officialQuestion(41), comments: [
        "Ampliar oportunidades de desenvolvimento profissional.",
        "Melhorar a comunicação entre as áreas.",
        "Ter mais reconhecimento pelas entregas da equipe.",
      ] },
    ],
    words: [
      { label: "Equipe", value: 28 }, { label: "Oportunidade", value: 21 },
      { label: "Aprendizado", value: 18 }, { label: "Estabilidade", value: 14 },
      { label: "Desenvolvimento", value: 11 }, { label: "Outros", value: 8 },
    ],
  },
};

export function filterManagementSegments(filters: ManagementFilters) {
  return mockManagement.segments.filter((segment) =>
    (!filters.regional || segment.regional === filters.regional)
    && (!filters.area || segment.area === filters.area)
    && (!filters.base || segment.base === filters.base)
    && (!filters.cnpj || segment.cnpj === filters.cnpj),
  );
}

export function filterManagementAttention(filters: ManagementFilters) {
  return mockManagement.attention.filter((item) =>
    (!filters.regional || item.regional === filters.regional)
    && (!filters.area || item.area === filters.area)
    && (!filters.base || item.base === filters.base)
    && (!filters.cnpj || item.cnpj === filters.cnpj),
  );
}

export function averageScore(values: number[]) {
  if (!values.length) return null;
  return Math.round(values.reduce((sum, value) => sum + value, 0) / values.length);
}

export function isManagementSegmentProtected(filters: ManagementFilters) {
  const matched = filterManagementSegments(filters);
  return matched.length > 0 && matched.every((segment) => segment.protected);
}

export function filterManagementPriorities(filters: ManagementFilters) {
  return mockManagement.priorityItems.filter((item) =>
    (!filters.regional || item.regional === filters.regional)
    && (!filters.area || item.area === filters.area)
    && (!filters.base || item.base === filters.base)
    && (!filters.cnpj || item.cnpj === filters.cnpj),
  );
}
