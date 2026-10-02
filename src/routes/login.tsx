import { useEffect, useState, type FormEvent } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { LanguageSelector } from "../components/layout/LanguageSelector";
import { ApiError, apiUrl } from "../lib/api";
import { getCurrentUser, requestEmailCode, verifyEmailCode } from "../services/auth";

export const Route = createFileRoute("/login")({
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const [emailFormOpen, setEmailFormOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [codeRequested, setCodeRequested] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const authError = new URLSearchParams(window.location.search).get("auth_error");
    if (authError) {
      const messages: Record<string, string> = {
        feishu_disabled: "O acesso pelo Feishu está temporariamente indisponível.",
        invalid_state: "Não foi possível validar o acesso. Inicie novamente pelo Feishu.",
        expired_state: "A solicitação de acesso expirou. Inicie novamente pelo Feishu.",
      };
      setNotice(messages[authError] ?? "Não foi possível concluir o acesso pelo Feishu. Tente novamente.");
    }
    let active = true;
    getCurrentUser().then(() => {
      if (active) void navigate({ to: "/home", replace: true });
    }).catch(() => undefined);
    return () => { active = false; };
  }, [navigate]);

  async function handleEmailSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotice("");
    setIsBusy(true);
    try {
      if (!codeRequested) {
        await requestEmailCode(email);
        setCodeRequested(true);
        setNotice("Se o endereço puder receber acesso, enviaremos um código. Verifique seu e-mail.");
      } else {
        await verifyEmailCode(email, code);
        await navigate({ to: "/home", replace: true });
      }
    } catch (error) {
      if (error instanceof ApiError && error.status === 503) {
        setNotice("Não foi possível concluir o acesso agora. Tente novamente em alguns minutos.");
      } else if (error instanceof ApiError && (error.status === 400 || error.status === 403 || error.status === 409 || error.status === 422)) {
        setNotice("Não foi possível validar o acesso. Confira os dados ou solicite um novo código.");
      } else {
        setNotice("Não foi possível conectar ao serviço de acesso. Tente novamente.");
      }
    } finally {
      setIsBusy(false);
    }
  }

  function handleFeishuLogin() {
    window.location.href = apiUrl("/api/auth/feishu/login");
  }

  return (
    <div className="login-page">
      <LanguageSelector className="login-page__languages" />
      <div className="login-page__content">
        <section className="login-card" aria-labelledby="login-title">
          <p className="login-card__brand">J&amp;T EXPRESS</p>
          <h1 className="login-card__title" id="login-title">
            Acesse a plataforma
          </h1>
          <p className="login-card__product">Pesquisa de Clima</p>
          <p className="login-card__description">
            Ambiente sigiloso para ouvir, entender e acompanhar a experiência dos colaboradores.
          </p>

              <button
            className="login-button login-button--primary"
            type="button"
            onClick={handleFeishuLogin}
          >
            <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
              <path
                d="M13 5h5a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-5M10 8l4 4-4 4m4-4H4"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.8"
              />
            </svg>
            Entrar com Feishu
          </button>

          <div className="login-divider" aria-hidden="true">
            <span>ou</span>
          </div>

          <button
            className="login-button login-button--secondary"
            type="button"
            aria-expanded={emailFormOpen}
            aria-controls="alternate-email-form"
            onClick={() => {
              setEmailFormOpen((isOpen) => !isOpen);
              setNotice("");
            }}
          >
            <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
              <rect
                x="3.5"
                y="5.5"
                width="17"
                height="13"
                rx="2"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
              />
              <path
                d="m4.5 7 7.5 5.5L19.5 7"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.7"
              />
            </svg>
            Entrar com e-mail alternativo
          </button>

          {emailFormOpen && (
            <form
              className="login-email-form"
              id="alternate-email-form"
              onSubmit={handleEmailSubmit}
            >
              <label htmlFor="alternate-email">E-mail</label>
              <input autoComplete="email" id="alternate-email" name="email" onChange={(event) => setEmail(event.target.value)} placeholder="nome@empresa.com" required type="email" value={email} disabled={codeRequested} />
              {codeRequested && <><label htmlFor="alternate-code">Código de acesso</label><input id="alternate-code" inputMode="numeric" autoComplete="one-time-code" maxLength={6} onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))} pattern="[0-9]{6}" placeholder="Digite o código de 6 dígitos" required type="text" value={code} /></>}
              <button className="login-button login-button--email" disabled={isBusy || (codeRequested && code.length !== 6)} type="submit">
                {isBusy ? "Aguarde…" : codeRequested ? "Validar código" : "Receber código de acesso"}
              </button>
              {codeRequested && <button className="login-code-back" type="button" onClick={() => { setCodeRequested(false); setCode(""); setNotice(""); }}>Usar outro e-mail</button>}
            </form>
          )}

          {notice && (
            <p className="login-notice" role="status">
              {notice}
            </p>
          )}

          <div className="login-privacy">
            <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
              <path
                d="M12 3.5 19 6v5.3c0 4.4-2.9 7.5-7 9.2-4.1-1.7-7-4.8-7-9.2V6l7-2.5Z"
                fill="none"
                stroke="currentColor"
                strokeLinejoin="round"
                strokeWidth="1.6"
              />
              <path
                d="m9 12 2 2 4-4"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.6"
              />
            </svg>
            <p>
              Suas respostas são confidenciais. Sua identidade de acesso não será vinculada ao
              conteúdo das respostas.
            </p>
          </div>

          <nav className="login-help-links" aria-label="Acesso e ajuda">
            <button
              type="button"
              onClick={() => setNotice("Solicitações de acesso serão disponibilizadas em uma próxima etapa.")}
            >
              Solicitar acesso
            </button>
            <span aria-hidden="true">·</span>
            <button
              type="button"
              onClick={() => setNotice("As informações de ajuda serão disponibilizadas em uma próxima etapa.")}
            >
              Preciso de ajuda
            </button>
          </nav>
        </section>
      </div>
    </div>
  );
}
