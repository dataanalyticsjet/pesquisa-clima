import type { SurveyOption, SurveyQuestion } from "../data/mockSurvey";
import type { SurveyDefinition } from "../services/surveys";
import type { Locale } from "./context";

type QuestionTranslation = { text: string; helper?: string; placeholder?: string; low?: string; high?: string; options?: Record<string, string> };

export const translatedSections: Record<string, string> = {
  IDENTIFICACAO: "运营区域信息",
  CONDICOES: "工作条件与组织安排",
  JORNADA: "工作时间",
  LIDERANCA: "领导力与沟通",
  AMBIENTE: "工作环境、尊重与安全",
  ETICA: "道德与合规",
  DESENVOLVIMENTO: "认可与发展",
  REMUNERACAO: "薪酬与福利",
  SAUDE: "健康、福祉与平衡",
  CONDICOES_AMBIENTE: "工作环境与条件",
  PERMANENCIA: "留任与企业归属感",
  PERCEPCAO: "整体印象",
  SUA_VOZ: "员工之声",
};

export const translatedSurveyTitle = "2026年员工氛围调查";
const likertOptions: Record<string, string> = {
  "1": "完全不同意",
  "2": "不同意",
  "3": "既不同意也不反对",
  "4": "同意",
  "5": "完全同意",
};

const questions: Record<string, QuestionTranslation> = {
  Q01: { text: "您所属的区域是？", placeholder: "选择区域" },
  Q02: { text: "您所在的服务中心/工作单位是？", placeholder: "选择服务中心/单位" },
  Q03: { text: "您的工作属性是：", options: { OPERATIONAL: "运营", ADMINISTRATIVE: "行政" } },
  Q04: { text: "我拥有完成工作所需的适当设施、工具和资源。" },
  Q05: { text: "内部流程和工作安排有助于我完成工作。" },
  Q06: { text: "关于工作所需的设施和资源，您认为哪些方面需要改进？", helper: "您可以选择多个选项。", options: {
    OPT_01: "工作空间或工位", OPT_02: "桌椅或其他家具", OPT_03: "台式电脑或笔记本电脑", OPT_04: "显示器、鼠标、键盘、耳机或其他配件", OPT_05: "设备的维护状况", OPT_06: "设备维修或更换", OPT_07: "工作系统或工具", OPT_08: "其他", OPT_09: "我认为无需改进",
  } },
  Q07: { text: "在大多数工作日，我都能在正常工作时间内完成工作。" },
  Q08: { text: "您通常多久会超出正常工作时间工作？", options: { OPT_01: "从不", OPT_02: "很少", OPT_03: "每月几次", OPT_04: "每周几次", OPT_05: "几乎每天" } },
  Q09: { text: "当工作时间延长时，主要原因是什么？", options: {
    OPT_01: "工作量过大", OPT_02: "团队人手不足", OPT_03: "期限或目标难以在正常工作时间内完成", OPT_04: "系统、工具或设备出现问题", OPT_05: "组织或计划不足", OPT_06: "依赖其他部门或流程", OPT_07: "领导提出的要求或任务", OPT_08: "运营需要", OPT_09: "流程返工或错误", OPT_10: "其他原因", OPT_11: "我的工作时间通常不会延长",
  } },
  Q10: { text: "您认为哪些措施最能帮助减少您所在区域的超时工作情况？", options: {
    OPT_01: "更好地规划和组织工作", OPT_02: "增加团队人数", OPT_03: "更合理地分配工作", OPT_04: "改进系统和工具", OPT_05: "重新审视目标和期限", OPT_06: "加强部门间的组织与协作", OPT_07: "减少返工", OPT_08: "领导更好地关注工作时间", OPT_09: "更清晰地确定优先事项", OPT_10: "其他措施",
  } },
  Q11: { text: "我的领导以尊重、专业和公正的态度对待我。" },
  Q12: { text: "我能清楚了解自己的职责、优先事项以及工作要求。" },
  Q13: { text: "我的领导会分享对工作有重要影响的信息和变化。" },
  Q14: { text: "有疑问、遇到困难或需要指导时，我可以主动联系领导。" },
  Q15: { text: "我的领导会持续就我的工作给予反馈。" },
  Q16: { text: "我觉得工作环境尊重彼此、乐于协作，大家互相支持。" },
  Q17: { text: "我在工作环境中的人身和心理安全得到保障。" },
  Q18: { text: "我觉得公司保持着没有骚扰和歧视的工作环境。" },
  Q19: { text: "我认为每个人都受到尊重和公平对待，不因个人特征而有所区别。" },
  Q20: { text: "我可以放心表达与工作有关的意见、疑问或困难。" },
  Q21: { text: "我了解Benfen举报渠道，并知道在需要时如何使用。" },
  Q22: { text: "我相信通过Benfen举报渠道反映的问题会得到恰当、公正的处理。" },
  Q23: { text: "我可以放心举报，不必担心遭到报复或受到负面影响。" },
  Q24: { text: "我认为领导的行为符合道德准则和公司规定。" },
  Q25: { text: "我的工作和成果会得到认可。" },
  Q26: { text: "我能看到自己在公司发展的机会。" },
  Q27: { text: "我认为薪酬与我的工作内容和职责相符。" },
  Q28: { text: "我认为公司提供的福利能够满足我的需求。" },
  Q29: { text: "我感受到公司关心员工的健康、福祉和工作条件。" },
  Q30: { text: "我能够在工作和个人生活之间保持适当的平衡。" },
  Q31: { text: "遇到与工作有关的困难时，我知道可以在公司哪里寻求帮助或指导。" },
  Q32: { text: "本单位的卫生间保持卫生、设施完好且运行正常吗？" },
  Q34: { text: "用餐空间能够满足员工人数的需要。" },
  Q35: { text: "微波炉、冰箱等用餐辅助设备能够满足员工的需要。" },
  Q36: { text: "我计划在未来12个月继续在J&T Express工作。" },
  Q37: { text: "我为在J&T Express工作感到自豪。" },
  Q38: { text: "哪些因素最可能影响您离开公司的决定？", helper: "请选择最主要的一项。", options: {
    OPT_01: "薪酬", OPT_02: "福利", OPT_03: "领导/管理", OPT_04: "工作量或工作时间", OPT_05: "工作环境或氛围", OPT_06: "缺乏认可", OPT_07: "缺少发展机会", OPT_08: "工作设施或条件", OPT_09: "工作流程与组织安排", OPT_10: "与同事/团队的关系", OPT_11: "距离/通勤", OPT_12: "工作内容与预期不同", OPT_13: "个人原因", OPT_14: "收到其他公司的更好录用机会", OPT_15: "其他", OPT_16: "目前没有离职打算",
  } },
  Q39: { text: "请用0至10分评价，您有多大可能向他人推荐J&T Express作为理想的工作场所？", low: "不推荐", high: "一定会推荐" },
  Q40: { text: "您所在区域可以采取哪些改变来更好地安排工作时间？", helper: "开放式回答，可选。", placeholder: "请输入您的回答（选答）" },
  Q41: { text: "公司可以在哪些方面改进，以提升您的工作体验？", helper: "开放式回答，可选。", placeholder: "请输入您的回答（选答）" },
  Q42: { text: "您最看重在J&T Express工作的哪一点？", helper: "请用一个词回答，可选。", placeholder: "一个词（选答）" },
};

const introParagraphs = [
  "您的声音是我们不断进步的一部分。",
  "我们希望倾听您在J&T Express的体验和想法。",
  "本调查为您提供一个真诚分享的空间，您可以谈谈工作环境、领导力、职场关系、工作条件以及日常工作中的其他方面。",
  "您的回答将帮助我们了解做得好的方面、发现改进机会，并采取具体行动，共同营造更加尊重、安全、健康和积极的工作环境。",
  "本调查为匿名调查。回答将以汇总形式分析，以保护隐私，并让您能够自由、坦诚地表达看法。",
  "请真诚参与。",
  "每一份意见都能帮助我们更好地了解团队的实际情况，并共同规划下一步。",
  "倾听以便了解。\n了解以便行动。\n携手共同进步。",
];

export function sectionLabel(code: string, original: string, locale: Locale) {
  return locale === "zh" ? translatedSections[code] ?? original : original;
}

export function surveyTitle(code: string, original: string, locale: Locale) {
  return locale === "zh" && code === "CLIMATE_2026" ? translatedSurveyTitle : original;
}

export function questionText(code: string, original: string, locale: Locale) {
  return locale === "zh" ? questions[code.toUpperCase()]?.text ?? original : original;
}

export function questionHelper(code: string, original: string | undefined, locale: Locale) {
  return locale === "zh" ? questions[code.toUpperCase()]?.helper ?? original : original;
}

export function questionPlaceholder(code: string, original: string | undefined, locale: Locale) {
  return locale === "zh" ? questions[code.toUpperCase()]?.placeholder ?? original : original;
}

export function questionScaleLabel(code: string, side: "low" | "high", original: string | undefined, locale: Locale) {
  return locale === "zh" ? questions[code.toUpperCase()]?.[side] ?? original : original;
}

export function optionLabel(questionCode: string, option: SurveyOption, locale: Locale, questionType?: SurveyQuestion["type"]) {
  if (locale !== "zh") return option.label;
  if (questionType === "likert") return likertOptions[option.value] ?? option.label;
  return questions[questionCode.toUpperCase()]?.options?.[option.value] ?? option.label;
}

export function introText(original: string | null | undefined, locale: Locale) {
  if (!original || locale !== "zh") return original ?? "";
  const paragraphs = original.split(/\n\s*\n/);
  return paragraphs.map((paragraph, index) => introParagraphs[index] ?? paragraph).join("\n\n");
}

export function surveyQuestionView<T extends SurveyQuestion>(question: T, locale: Locale): T {
  return {
    ...question,
    text: questionText(question.id, question.text, locale),
    helperText: questionHelper(question.id, question.helperText, locale),
    placeholder: questionPlaceholder(question.id, question.placeholder, locale),
    lowLabel: questionScaleLabel(question.id, "low", question.lowLabel, locale),
    highLabel: questionScaleLabel(question.id, "high", question.highLabel, locale),
    options: question.options?.map((option) => ({ ...option, label: optionLabel(question.id, option, locale, question.type) })),
  };
}

export function localizedSurvey(survey: SurveyDefinition, locale: Locale): SurveyDefinition {
  return {
    ...survey,
    title: surveyTitle(survey.code, survey.title, locale),
    intro_text: introText(survey.intro_text, locale),
    completion_text: locale === "zh" && survey.completion_text === "Obrigada por participar!"
      ? "感谢您的参与！"
      : survey.completion_text,
    sections: survey.sections.map((section) => ({
      ...section,
      name: sectionLabel(section.id, section.name, locale),
    })),
    questions: survey.questions.map((question) => surveyQuestionView(question, locale)),
  };
}
