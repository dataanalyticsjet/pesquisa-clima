export type LikertOption = {
  value: 1 | 2 | 3 | 4 | 5;
  label: string;
};

export type SurveyQuestion = {
  id: string;
  text: string;
};

export type SurveyPillar = {
  id: string;
  name: string;
  questions: SurveyQuestion[];
};

export type SurveyDefinition = {
  id: string;
  title: string;
  status: "ACTIVE";
  description: string;
  estimatedTimeMinutes: number;
  pillars: SurveyPillar[];
  scale: LikertOption[];
};

// DEMO ONLY
// Replace with survey API when backend is implemented.
export const mockSurvey: SurveyDefinition = {
  id: "clima-2026",
  title: "Pesquisa de Clima Organizacional 2026",
  status: "ACTIVE",
  description: "Queremos ouvir você e entender melhor sua experiência no ambiente de trabalho.",
  estimatedTimeMinutes: 8,
  pillars: [
    {
      id: "lideranca",
      name: "Liderança",
      questions: [
        { id: "lideranca-1", text: "Meu gestor comunica claramente as prioridades da equipe." },
        { id: "lideranca-2", text: "Recebo direcionamento adequado para realizar meu trabalho." },
        { id: "lideranca-3", text: "Minha liderança escuta as opiniões da equipe." },
      ],
    },
    {
      id: "ambiente",
      name: "Ambiente",
      questions: [
        { id: "ambiente-1", text: "Tenho um ambiente adequado para realizar meu trabalho." },
        { id: "ambiente-2", text: "Existe respeito entre os colegas da minha equipe." },
        { id: "ambiente-3", text: "Sinto que posso expressar minha opinião no ambiente de trabalho." },
      ],
    },
    {
      id: "comunicacao",
      name: "Comunicação",
      questions: [
        { id: "comunicacao-1", text: "Recebo informações importantes em tempo adequado." },
        { id: "comunicacao-2", text: "A comunicação entre áreas funciona de maneira eficiente." },
        { id: "comunicacao-3", text: "Tenho clareza sobre mudanças que impactam meu trabalho." },
      ],
    },
    {
      id: "reconhecimento",
      name: "Reconhecimento",
      questions: [
        { id: "reconhecimento-1", text: "Meu trabalho é reconhecido." },
        { id: "reconhecimento-2", text: "Sinto que meu desempenho é valorizado." },
        { id: "reconhecimento-3", text: "Recebo feedback sobre meu trabalho." },
      ],
    },
  ],
  scale: [
    { value: 1, label: "Discordo totalmente" },
    { value: 2, label: "Discordo" },
    { value: 3, label: "Neutro" },
    { value: 4, label: "Concordo" },
    { value: 5, label: "Concordo totalmente" },
  ],
};
