export type LikertOption = {
  value: 1 | 2 | 3 | 4 | 5;
  label: string;
};

export type SurveyAnswer = number | string | string[];
export type SurveyQuestionType =
  | "select"
  | "single_choice"
  | "multiple_choice"
  | "likert"
  | "nps"
  | "textarea"
  | "short_text";

export type SurveyOption = {
  value: string;
  label: string;
  exclusive?: boolean;
};

export type SurveyQuestion = {
  id: string;
  number: number;
  sectionId: string;
  type: SurveyQuestionType;
  text: string;
  required: boolean;
  helperText?: string;
  placeholder?: string;
  options?: SurveyOption[];
};

export type SurveySection = {
  id: string;
  name: string;
};

export type SurveyPillar = {
  id: string;
  name: string;
  questions: { id: string; text: string }[];
};

export type SurveyDefinition = {
  id: string;
  title: string;
  status: "ACTIVE";
  description: string;
  introduction: string[];
  sections: SurveySection[];
  questions: SurveyQuestion[];
  scale: LikertOption[];
  npsLabels: { low: string; high: string };
  /** Compatibility adapter for the unchanged management demo; the participant form uses sections and questions. */
  pillars: SurveyPillar[];
};

const options = (values: string[]): SurveyOption[] => values.map((label) => ({ value: label, label }));

// DEMO OPTIONS: regional names are specified for this demonstration. Unit and CNPJ values are fictitious
// placeholders because the official survey PDF does not provide those option lists.
const regionalOptions = options(["SPS", "SPN", "SPE", "PR", "PA", "BA", "MG", "CE", "RJ", "GP"]);
const unitDemoOptions = options([
  "DEMO — Unidade SPS",
  "DEMO — Unidade SPN",
  "DEMO — Unidade SPE",
  "DEMO — Unidade PR",
  "DEMO — Unidade PA",
  "DEMO — Unidade BA",
  "DEMO — Unidade MG",
  "DEMO — Unidade CE",
  "DEMO — Unidade RJ",
  "DEMO — Unidade GP",
]);
const cnpjDemoOptions = [
  { value: "DEMO-CNPJ-01", label: "DEMO — CNPJ demonstrativo 1" },
  { value: "DEMO-CNPJ-02", label: "DEMO — CNPJ demonstrativo 2" },
  { value: "unknown", label: "Não sei informar" },
];
const questions: SurveyQuestion[] = [
  { id: "q01", number: 1, sectionId: "identificacao", type: "select", text: "Qual é a sua Regional?", required: true, placeholder: "Selecionar Regional", options: regionalOptions },
  { id: "q02", number: 2, sectionId: "identificacao", type: "select", text: "Qual é a sua Base/Unidade de atuação?", required: true, placeholder: "Selecionar Base/Unidade", options: unitDemoOptions },
  { id: "q03", number: 3, sectionId: "identificacao", type: "select", text: "Em qual CNPJ você está registrado(a)?", helperText: "Essa informação pode ser consultada na sua Carteira de Trabalho Digital.", required: true, placeholder: "Selecionar CNPJ/Unidade", options: cnpjDemoOptions },
  { id: "q04", number: 4, sectionId: "condicoes", type: "likert", text: "Tenho estrutura, ferramentas e recursos adequados para realizar meu trabalho.", required: true },
  { id: "q05", number: 5, sectionId: "condicoes", type: "likert", text: "Os processos internos e a organização do trabalho facilitam a realização das minhas atividades.", required: true },
  { id: "q06", number: 6, sectionId: "condicoes", type: "multiple_choice", text: "Em relação à estrutura e aos recursos disponíveis para o seu trabalho, o que você considera que precisa ser melhorado?", helperText: "Você pode selecionar mais de uma opção.", required: true, options: [
    ...options(["Espaço ou posto de trabalho", "Mesa, cadeira ou mobiliário", "Computador ou notebook", "Monitor, mouse, teclado, headset ou outros acessórios", "Estado de conservação dos equipamentos", "Manutenção ou substituição de equipamentos", "Sistemas ou ferramentas de trabalho", "Outro"]),
    { value: "Não identifico necessidade de melhoria", label: "Não identifico necessidade de melhoria", exclusive: true },
  ] },
  { id: "q07", number: 7, sectionId: "jornada", type: "likert", text: "Na maior parte dos dias, consigo realizar minhas atividades dentro da minha jornada normal de trabalho.", required: true },
  { id: "q08", number: 8, sectionId: "jornada", type: "single_choice", text: "Trabalhar além da jornada normal, isso acontece com que frequência?", required: true, options: options(["Nunca", "Raramente", "Algumas vezes no mês", "Algumas vezes na semana", "Quase todos os dias"]) },
  { id: "q09", number: 9, sectionId: "jornada", type: "single_choice", text: "Quando minha jornada de trabalho se estende, qual é o principal motivo?", required: true, options: options(["Volume elevado de trabalho", "Falta de pessoas na equipe", "Prazos ou metas difíceis de cumprir dentro da jornada", "Problemas em sistemas, ferramentas ou equipamentos", "Falta de organização ou planejamento", "Dependência de outras áreas ou processos", "Solicitações ou demandas da liderança", "Necessidade da operação", "Retrabalho ou falhas nos processos", "Outro motivo", "Minha jornada normalmente não se estende"]) },
  { id: "q10", number: 10, sectionId: "jornada", type: "single_choice", text: "Na sua opinião, o que mais ajudaria a reduzir situações de jornada excessiva na sua área?", required: true, options: options(["Melhor planejamento e organização das atividades", "Aumento do número de pessoas na equipe", "Melhor distribuição das atividades", "Melhoria dos sistemas e ferramentas", "Revisão de metas e prazos", "Melhor organização e integração entre as áreas", "Redução de retrabalho", "Maior acompanhamento da liderança sobre a jornada", "Melhor definição de prioridades", "Outra ação"]) },
  { id: "q11", number: 11, sectionId: "lideranca", type: "likert", text: "Minha liderança me trata com respeito, profissionalismo e imparcialidade.", required: true },
  { id: "q12", number: 12, sectionId: "lideranca", type: "likert", text: "Recebo orientações claras sobre minhas responsabilidades, prioridades e o que é esperado do meu trabalho.", required: true },
  { id: "q13", number: 13, sectionId: "lideranca", type: "likert", text: "Minha liderança compartilha informações importantes e mudanças que impactam meu trabalho.", required: true },
  { id: "q14", number: 14, sectionId: "lideranca", type: "likert", text: "Tenho abertura para procurar minha liderança quando preciso tirar dúvidas, apresentar dificuldades ou pedir orientação.", required: true },
  { id: "q15", number: 15, sectionId: "lideranca", type: "likert", text: "Recebo feedbacks constantemente da minha liderança referente o trabalho que realizo.", required: true },
  { id: "q16", number: 16, sectionId: "ambiente", type: "likert", text: "Sinto que trabalho em um ambiente respeitoso, colaborativo e com apoio entre as pessoas.", required: true },
  { id: "q17", number: 17, sectionId: "ambiente", type: "likert", text: "Sinto-me seguro(a) física e emocionalmente no meu ambiente de trabalho.", required: true },
  { id: "q18", number: 18, sectionId: "ambiente", type: "likert", text: "Sinto que a empresa mantém um ambiente de trabalho livre de assédio e discriminação.", required: true },
  { id: "q19", number: 19, sectionId: "ambiente", type: "likert", text: "Percebo que as pessoas são tratadas com respeito e justiça, independentemente de suas características pessoais.", required: true },
  { id: "q20", number: 20, sectionId: "ambiente", type: "likert", text: "Sinto segurança para expressar opiniões, dúvidas ou dificuldades relacionadas ao meu trabalho.", required: true },
  { id: "q21", number: 21, sectionId: "etica", type: "likert", text: "Conheço o Canal de Denúncias Benfen e sei como utilizá-lo caso seja necessário.", required: true },
  { id: "q22", number: 22, sectionId: "etica", type: "likert", text: "Confio que uma situação relatada pelo Canal de Denúncias Benfen será tratada de forma adequada e imparcial.", required: true },
  { id: "q23", number: 23, sectionId: "etica", type: "likert", text: "Sinto segurança para realizar um relato ou denúncia sem medo de sofrer retaliação ou consequências negativas.", required: true },
  { id: "q24", number: 24, sectionId: "etica", type: "likert", text: "Percebo que minha liderança atua de forma ética e coerente com as regras da empresa.", required: true },
  { id: "q25", number: 25, sectionId: "desenvolvimento", type: "likert", text: "Sinto que meu trabalho e minhas entregas são reconhecidos.", required: true },
  { id: "q26", number: 26, sectionId: "desenvolvimento", type: "likert", text: "Consigo visualizar oportunidades de desenvolvimento e crescimento profissional na empresa.", required: true },
  { id: "q27", number: 27, sectionId: "remuneracao", type: "likert", text: "Considero minha remuneração compatível com minhas atividades e responsabilidades.", required: true },
  { id: "q28", number: 28, sectionId: "remuneracao", type: "likert", text: "Considero que os benefícios oferecidos pela empresa atendem às minhas necessidades.", required: true },
  { id: "q29", number: 29, sectionId: "saude", type: "likert", text: "Percebo que a empresa se preocupa com a saúde, o bem-estar e as condições de trabalho dos colaboradores.", required: true },
  { id: "q30", number: 30, sectionId: "saude", type: "likert", text: "Consigo manter um equilíbrio adequado entre minha vida profissional e pessoal.", required: true },
  { id: "q31", number: 31, sectionId: "saude", type: "likert", text: "Sei onde buscar apoio ou orientação dentro da empresa quando enfrento alguma dificuldade relacionada ao trabalho.", required: true },
  { id: "q32", number: 32, sectionId: "condicoes-ambiente", type: "likert", text: "Os sanitários da unidade são mantidos limpos e em boas condições de higiene.", required: true },
  { id: "q33", number: 33, sectionId: "condicoes-ambiente", type: "likert", text: "Os sanitários estão conservados e em bom estado de funcionamento.", required: true },
  { id: "q34", number: 34, sectionId: "condicoes-ambiente", type: "likert", text: "O espaço disponível para realizar as refeições é adequado à quantidade de colaboradores.", required: true },
  { id: "q35", number: 35, sectionId: "condicoes-ambiente", type: "likert", text: "Os equipamentos disponíveis para apoio às refeições, como micro-ondas e geladeira, são adequados às necessidades dos colaboradores.", required: true },
  { id: "q36", number: 36, sectionId: "permanencia", type: "likert", text: "Pretendo continuar trabalhando na J&T Express nos próximos 12 meses.", required: true },
  { id: "q37", number: 37, sectionId: "permanencia", type: "likert", text: "Tenho orgulho de trabalhar na J&T Express.", required: true },
  { id: "q38", number: 38, sectionId: "permanencia", type: "single_choice", text: "Qual fator que mais poderia influenciar na sua decisão de sair da empresa?", helperText: "Escolha o principal.", required: true, options: options(["Remuneração", "Benefícios", "Liderança/Gestão", "Carga ou jornada de trabalho", "Ambiente ou clima de trabalho", "Falta de reconhecimento", "Falta de oportunidade de crescimento", "Estrutura ou condições de trabalho", "Processos e organização do trabalho", "Relacionamento com colegas/equipe", "Distância/deslocamento", "Atividade diferente da expectativa", "Questões pessoais", "Receber uma proposta melhor de outra empresa", "Outro", "No momento, não penso em sair da empresa"]) },
  { id: "q39", number: 39, sectionId: "percepcao", type: "nps", text: "Em uma escala de 0 a 10, o quanto você recomendaria a J&T Express como um bom lugar para trabalhar?", required: true },
  { id: "q40", number: 40, sectionId: "sua-voz", type: "textarea", text: "Que mudança ajudaria a organizar melhor a jornada de trabalho na sua área?", helperText: "Resposta aberta. Opcional.", required: false, placeholder: "Escreva sua resposta (opcional)" },
  { id: "q41", number: 41, sectionId: "sua-voz", type: "textarea", text: "O que a empresa poderia melhorar para tornar sua experiência de trabalho melhor?", helperText: "Resposta aberta. Opcional.", required: false, placeholder: "Escreva sua resposta (opcional)" },
  { id: "q42", number: 42, sectionId: "sua-voz", type: "short_text", text: "O que você mais valoriza em trabalhar na J&T Express?", helperText: "Responda em uma palavra. Opcional.", required: false, placeholder: "Uma palavra (opcional)" },
];

export const mockSurvey: SurveyDefinition = {
  id: "clima-2026",
  title: "Pesquisa de Clima Organizacional 2026",
  status: "ACTIVE",
  description: "Queremos ouvir você e conhecer sua experiência na J&T Express.",
  introduction: [
    "Sua voz faz parte da nossa evolução.",
    "Queremos ouvir você e conhecer sua experiência na J&T Express.",
    "Esta pesquisa é um espaço para compartilhar, de forma sincera, suas percepções sobre o ambiente de trabalho, liderança, relações profissionais, condições de trabalho e outros aspectos que fazem parte do seu dia a dia.",
    "Suas respostas nos ajudarão a reconhecer o que estamos fazendo bem, identificar oportunidades de melhoria e direcionar ações concretas para construir um ambiente de trabalho cada vez mais respeitoso, seguro, saudável e positivo.",
    "A pesquisa é anônima e as respostas serão analisadas de forma consolidada, garantindo confidencialidade e liberdade para que você possa expressar sua percepção com transparência.",
    "Participe com sinceridade.",
    "Cada percepção contribui para entendermos melhor a realidade das nossas equipes e construirmos, juntos, os próximos passos.",
    "Escutar para entender.\nEntender para agir.\nEvoluir juntos.",
  ],
  sections: [
    { id: "identificacao", name: "IDENTIFICAÇÃO DA OPERAÇÃO" },
    { id: "condicoes", name: "CONDIÇÕES E ORGANIZAÇÃO DO TRABALHO" },
    { id: "jornada", name: "JORNADA DE TRABALHO" },
    { id: "lideranca", name: "LIDERANÇA E COMUNICAÇÃO" },
    { id: "ambiente", name: "AMBIENTE, RESPEITO E SEGURANÇA" },
    { id: "etica", name: "ÉTICA E COMPLIANCE" },
    { id: "desenvolvimento", name: "RECONHECIMENTO E DESENVOLVIMENTO" },
    { id: "remuneracao", name: "REMUNERAÇÃO E BENEFÍCIOS" },
    { id: "saude", name: "SAÚDE, BEM-ESTAR E EQUILÍBRIO" },
    { id: "condicoes-ambiente", name: "AMBIENTE E CONDIÇÕES DE TRABALHO" },
    { id: "permanencia", name: "PERMANÊNCIA E VÍNCULO COM A EMPRESA" },
    { id: "percepcao", name: "PERCEPÇÃO GERAL" },
    { id: "sua-voz", name: "SUA VOZ" },
  ],
  questions,
  scale: [
    { value: 1, label: "Discordo totalmente" },
    { value: 2, label: "Discordo" },
    { value: 3, label: "Nem concordo nem discordo" },
    { value: 4, label: "Concordo" },
    { value: 5, label: "Concordo totalmente" },
  ],
  npsLabels: { low: "Não recomendaria", high: "Recomendaria com certeza" },
  // Temporary bridge for mockManagement.ts, which remains untouched in this phase.
  // This old demo grouping exists only to preserve the /management preview until its own stage;
  // the collaborator questionnaire exclusively uses `sections` and `questions` above.
  pillars: [
    { id: "lideranca", name: "Liderança", questions: [
      { id: "lideranca-1", text: "Meu gestor comunica claramente as prioridades da equipe." },
      { id: "lideranca-2", text: "Recebo direcionamento adequado para realizar meu trabalho." },
      { id: "lideranca-3", text: "Minha liderança escuta as opiniões da equipe." },
    ] },
    { id: "ambiente", name: "Ambiente", questions: [
      { id: "ambiente-1", text: "Tenho um ambiente adequado para realizar meu trabalho." },
      { id: "ambiente-2", text: "Existe respeito entre os colegas da minha equipe." },
      { id: "ambiente-3", text: "Sinto que posso expressar minha opinião no ambiente de trabalho." },
    ] },
    { id: "comunicacao", name: "Comunicação", questions: [
      { id: "comunicacao-1", text: "Recebo informações importantes em tempo adequado." },
      { id: "comunicacao-2", text: "A comunicação entre áreas funciona de maneira eficiente." },
      { id: "comunicacao-3", text: "Tenho clareza sobre mudanças que impactam meu trabalho." },
    ] },
    { id: "reconhecimento", name: "Reconhecimento", questions: [
      { id: "reconhecimento-1", text: "Meu trabalho é reconhecido." },
      { id: "reconhecimento-2", text: "Sinto que meu desempenho é valorizado." },
      { id: "reconhecimento-3", text: "Recebo feedback sobre meu trabalho." },
    ] },
  ],
};
