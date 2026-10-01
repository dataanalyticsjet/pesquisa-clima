import { createFileRoute } from "@tanstack/react-router";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { mockManagement } from "../data/mockManagement";
import { mockSurvey } from "../data/mockSurvey";

export const Route = createFileRoute("/management/voice")({ component: ManagementVoice });

function ManagementVoice() {
  const { answers, words } = mockManagement.voice;
  return (
    <ManagementLayout>
      <ManagementPageTitle title="Sua Voz" description="Síntese demonstrativa das respostas abertas, sempre sem nomes ou identificação individual." />
      <p className="management-privacy-note"><span className="management-privacy-note__icon" aria-hidden="true">i</span><span>Respostas exibidas somente de forma consolidada. Nenhum nome, e-mail ou resposta identificável é apresentado.</span></p>
      <div className="voice-answer-grid">
        {answers.map((answer) => (
          <section className="voice-answer-card" key={answer.questionNumber}>
            <p className="management-eyebrow">Q{answer.questionNumber}</p>
            <h2>{answer.text}</h2>
            <ul>{answer.comments.map((comment, index) => <li key={answer.questionNumber + "-" + index}>“{comment}”</li>)}</ul>
            <p className="management-demo-note">Comentários fictícios e consolidados para demonstração.</p>
          </section>
        ))}
      </div>
      <section className="management-section voice-words" aria-labelledby="voice-words-title">
        <div className="management-section__heading"><div><p className="management-eyebrow">Q42 · PALAVRAS FREQUENTES</p><h2 id="voice-words-title">{mockSurvey.questions.find((question) => question.number === 42)?.text ?? "O que você mais valoriza em trabalhar na J&T Express?"}</h2></div></div>
        <div className="voice-word-cloud">{words.map((word) => <span key={word.label} style={{ fontSize: "clamp(.8rem, " + (0.8 + word.value / 32) + "rem, 1.45rem)" }}>{word.label}<small>{word.value}%</small></span>)}</div>
        <p className="management-demo-note">Termos mockados agregados; respostas individuais não são exibidas.</p>
      </section>
    </ManagementLayout>
  );
}
