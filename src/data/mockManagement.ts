import { mockSurvey } from "./mockSurvey";

// DEMO ONLY
// Replace with aggregated analytics API when backend is implemented.

export type ManagementDistribution = {
  positive: number;
  neutral: number;
  negative: number;
};

export type ManagementPillar = {
  id: string;
  name: string;
  score: number;
  distribution: ManagementDistribution;
  trend: number;
  evolution: { year: number; score: number }[];
  questions: { text: string; score: number }[];
};

export type ManagementAttention = {
  id: string;
  pillarId: string;
  pillar: string;
  score: number;
  criticality: "CRITICAL" | "ATTENTION" | "HEALTHY";
  reason: string;
  question: string;
  questionScore: number;
};

export const mockManagement = {
  survey: {
    title: "Pesquisa de Clima Organizacional 2026",
    status: "ACTIVE" as const,
    invited: 5842,
    responses: 4291,
    adherence: 73.45,
    overallScore: 72,
    attentionCount: 3,
  },
  overallEvolution: [
    { year: 2024, score: 68 },
    { year: 2025, score: 70 },
    { year: 2026, score: 72 },
  ],
  pillars: [
    {
      id: mockSurvey.pillars[0].id,
      name: mockSurvey.pillars[0].name,
      score: 62,
      distribution: { positive: 49, neutral: 18, negative: 33 },
      trend: -4,
      evolution: [
        { year: 2024, score: 68 },
        { year: 2025, score: 66 },
        { year: 2026, score: 62 },
      ],
      questions: [
        { text: mockSurvey.pillars[0].questions[0].text, score: 64 },
        { text: mockSurvey.pillars[0].questions[1].text, score: 65 },
        { text: mockSurvey.pillars[0].questions[2].text, score: 57 },
      ],
    },
    {
      id: mockSurvey.pillars[1].id,
      name: mockSurvey.pillars[1].name,
      score: 81,
      distribution: { positive: 76, neutral: 15, negative: 9 },
      trend: 3,
      evolution: [
        { year: 2024, score: 75 },
        { year: 2025, score: 78 },
        { year: 2026, score: 81 },
      ],
      questions: [
        { text: mockSurvey.pillars[1].questions[0].text, score: 79 },
        { text: mockSurvey.pillars[1].questions[1].text, score: 83 },
        { text: mockSurvey.pillars[1].questions[2].text, score: 81 },
      ],
    },
    {
      id: mockSurvey.pillars[2].id,
      name: mockSurvey.pillars[2].name,
      score: 67,
      distribution: { positive: 54, neutral: 19, negative: 27 },
      trend: -2,
      evolution: [
        { year: 2024, score: 70 },
        { year: 2025, score: 69 },
        { year: 2026, score: 67 },
      ],
      questions: [
        { text: mockSurvey.pillars[2].questions[0].text, score: 68 },
        { text: mockSurvey.pillars[2].questions[1].text, score: 59 },
        { text: mockSurvey.pillars[2].questions[2].text, score: 67 },
      ],
    },
    {
      id: mockSurvey.pillars[3].id,
      name: mockSurvey.pillars[3].name,
      score: 51,
      distribution: { positive: 29, neutral: 25, negative: 46 },
      trend: -7,
      evolution: [
        { year: 2024, score: 64 },
        { year: 2025, score: 58 },
        { year: 2026, score: 51 },
      ],
      questions: [
        { text: mockSurvey.pillars[3].questions[0].text, score: 43 },
        { text: mockSurvey.pillars[3].questions[1].text, score: 51 },
        { text: mockSurvey.pillars[3].questions[2].text, score: 59 },
      ],
    },
  ] satisfies ManagementPillar[],
  attention: [
    {
      id: "reconhecimento",
      pillarId: "reconhecimento",
      pillar: "Reconhecimento",
      score: 51,
      criticality: "CRITICAL",
      reason: "46% das avaliações são negativas.",
      question: "Meu trabalho é reconhecido.",
      questionScore: 43,
    },
    {
      id: "lideranca",
      pillarId: "lideranca",
      pillar: "Liderança",
      score: 62,
      criticality: "ATTENTION",
      reason: "33% das avaliações são negativas.",
      question: "Minha liderança escuta as opiniões da equipe.",
      questionScore: 57,
    },
    {
      id: "comunicacao",
      pillarId: "comunicacao",
      pillar: "Comunicação",
      score: 67,
      criticality: "ATTENTION",
      reason: "Queda de 2 pontos no comparativo simulado.",
      question: "A comunicação entre áreas funciona de maneira eficiente.",
      questionScore: 59,
    },
  ] satisfies ManagementAttention[],
  regionalAdherence: [
    { region: "SPS", adherence: 82 },
    { region: "SPE", adherence: 79 },
    { region: "PR", adherence: 77 },
    { region: "MG", adherence: 74 },
    { region: "SPN", adherence: 71 },
    { region: "RJ", adherence: 68 },
    { region: "PA", adherence: 63 },
  ],
  actionPlans: [
    {
      id: "plano-reconhecimento",
      pillar: "Reconhecimento",
      problem: "Baixo índice de reconhecimento percebido.",
      action: "Criar rotina mensal de reconhecimento de resultados.",
      owner: "People",
      dueDate: "30/11/2026",
      status: "IN_PROGRESS" as const,
      currentScore: 51,
      targetScore: 70,
    },
    {
      id: "plano-comunicacao",
      pillar: "Comunicação",
      problem: "Baixa percepção de comunicação entre áreas.",
      action: "Criar reunião mensal interáreas e resumo executivo.",
      owner: "People + Operações",
      dueDate: "15/12/2026",
      status: "PLANNED" as const,
      currentScore: 67,
      targetScore: 75,
    },
  ],
};

export type ManagementActionPlan = (typeof mockManagement.actionPlans)[number];
