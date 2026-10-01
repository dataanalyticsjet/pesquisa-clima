import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { SurveyAnswer } from "../../data/mockSurvey";

export type SurveyStep = "intro" | "questions" | "review" | "success";

type SurveyDemoContextValue = {
  answers: Record<string, SurveyAnswer>;
  isCompleted: boolean;
  currentQuestionIndex: number;
  step: SurveyStep;
  setAnswer: (questionId: string, value: SurveyAnswer) => void;
  setCurrentQuestionIndex: (index: number) => void;
  setStep: (step: SurveyStep) => void;
  completeSurvey: () => void;
};

const SurveyDemoContext = createContext<SurveyDemoContextValue | null>(null);

export function SurveyDemoProvider({ children }: { children: ReactNode }) {
  const [answers, setAnswers] = useState<Record<string, SurveyAnswer>>({});
  const [isCompleted, setIsCompleted] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [step, setStep] = useState<SurveyStep>("intro");

  const value = useMemo(
    () => ({
      answers,
      isCompleted,
      currentQuestionIndex,
      step,
      setAnswer: (questionId: string, response: SurveyAnswer) => {
        setAnswers((current) => ({ ...current, [questionId]: response }));
      },
      setCurrentQuestionIndex,
      setStep,
      completeSurvey: () => {
        setIsCompleted(true);
        setStep("success");
      },
    }),
    [answers, currentQuestionIndex, isCompleted, step],
  );

  return <SurveyDemoContext.Provider value={value}>{children}</SurveyDemoContext.Provider>;
}

export function useSurveyDemo() {
  const context = useContext(SurveyDemoContext);
  if (!context) {
    throw new Error("useSurveyDemo deve ser usado dentro de SurveyDemoProvider.");
  }
  return context;
}
