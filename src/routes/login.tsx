import { useEffect, useState, type FormEvent } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { LanguageSelector } from "../components/layout/LanguageSelector";
import { ApiError, apiUrl } from "../lib/api";
import { clearFeishuPostLoginRedirect, getAuthenticatedLandingPath, markFeishuPostLoginRedirect } from "../lib/roleNavigation";
import { getCurrentUser, requestEmailCode, verifyEmailCode } from "../services/auth";
import { useI18n } from "../i18n/context";
import type { TranslationKey } from "../i18n/catalog";

export const Route = createFileRoute("/login")({
  component: LoginPage,
});

type EmailLoginStep = "initial" | "email" | "code";

function LoginPage() {
  const navigate = useNavigate();
  const [emailLoginStep, setEmailLoginStep] = useState<EmailLoginStep>("initial");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [notice, setNotice] = useState<TranslationKey | "">("");
  const { t } = useI18n();

  useEffect(() => {
    clearFeishuPostLoginRedirect();
    const authError = new URLSearchParams(window.location.search).get("auth_error");
    if (authError) {
      const messages: Record<string, TranslationKey> = {
        feishu_disabled: "login.feishuDisabled",
        invalid_state: "login.invalidState",
        expired_state: "login.expiredState",
      };
      setNotice(messages[authError] ?? "login.feishuError");
    }
    let active = true;
    getCurrentUser().then(({ user }) => {
      if (active) void navigate({ to: getAuthenticatedLandingPath(user.roles), replace: true });
    }).catch(() => undefined);
    return () => { active = false; };
  }, [navigate]);

  async function handleEmailSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const requestingCode = emailLoginStep === "email";
    setNotice("");
    setIsBusy(true);
    try {
      if (requestingCode) {
        await requestEmailCode(email);
        setCode("");
        setEmailLoginStep("code");
      } else {
        await verifyEmailCode(email, code);
        const { user } = await getCurrentUser();
        await navigate({ to: getAuthenticatedLandingPath(user.roles), replace: true });
      }
    } catch (error) {
      if (error instanceof ApiError && error.status >= 500) {
        setNotice(requestingCode ? "login.emailUnavailable" : "login.verificationUnavailable");
      } else if (error instanceof ApiError && error.status === 422) {
        setNotice(requestingCode ? "login.invalidEmail" : "login.codeInvalid");
      } else if (error instanceof ApiError && (error.status === 400 || error.status === 403 || error.status === 409)) {
        setNotice("login.codeInvalid");
      } else {
        setNotice("login.connectionError");
      }
    } finally {
      setIsBusy(false);
    }
  }

  async function handleResendCode() {
    setNotice("");
    setIsBusy(true);
    try {
      await requestEmailCode(email);
      setNotice("login.resendRequested");
    } catch (error) {
      if (error instanceof ApiError && error.status >= 500) {
        setNotice("login.emailUnavailable");
      } else if (error instanceof ApiError && error.status === 422) {
        setNotice("login.invalidEmail");
      } else {
        setNotice("login.connectionError");
      }
    } finally {
      setIsBusy(false);
    }
  }

  function handleFeishuLogin() {
    markFeishuPostLoginRedirect();
    window.location.href = apiUrl("/api/auth/feishu/login");
  }

  return (
    <div className="login-page">
      <LanguageSelector className="login-page__languages" />
      <div className="login-page__content">
        <section className="login-card" aria-labelledby="login-title">
          <img className="login-card__logo" src="/jt-express-logo.png" alt="J&T Express" />
          <h1 className="login-card__title" id="login-title">
            {t(emailLoginStep === "initial" ? "login.title" : emailLoginStep === "email" ? "login.emailStepTitle" : "login.codeStepTitle")}
          </h1>
          <p className="login-card__product">{t("login.product")}</p>
          {emailLoginStep === "initial" ? (
            <>
              <p className="login-card__description">{t("login.description")}</p>
              <button className="login-button login-button--primary" type="button" onClick={handleFeishuLogin}>
                <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
                  <path d="M13 5h5a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-5M10 8l4 4-4 4m4-4H4" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
                </svg>
                {t("login.feishu")}
              </button>
              <div className="login-divider" aria-hidden="true"><span>{t("login.or")}</span></div>
              <button className="login-button login-button--secondary" type="button" onClick={() => { setNotice(""); setEmailLoginStep("email"); }}>
                <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
                  <rect x="3.5" y="5.5" width="17" height="13" rx="2" fill="none" stroke="currentColor" strokeWidth="1.7" />
                  <path d="m4.5 7 7.5 5.5L19.5 7" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7" />
                </svg>
                {t("login.emailAlt")}
              </button>
            </>
          ) : (
            <div className="login-email-step">
              {emailLoginStep === "code" && <p className="login-code-sent" role="status">{t("login.codeSentTo", { email })}</p>}
              <form className="login-email-form" onSubmit={handleEmailSubmit}>
                {emailLoginStep === "email" ? (
                  <>
                    <label htmlFor="alternate-email">{t("login.emailPrompt")}</label>
                    <input autoComplete="email" id="alternate-email" name="email" onChange={(event) => setEmail(event.target.value)} placeholder={t("login.emailPlaceholder")} required type="email" value={email} />
                  </>
                ) : (
                  <>
                    <label htmlFor="alternate-code">{t("login.codePrompt")}</label>
                    <input autoComplete="one-time-code" id="alternate-code" inputMode="numeric" maxLength={6} onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))} pattern="[0-9]{6}" placeholder={t("login.codePlaceholder")} required type="text" value={code} />
                  </>
                )}
                <button className="login-button login-button--email" disabled={isBusy || (emailLoginStep === "code" && code.length !== 6)} type="submit">
                  {isBusy ? t("login.wait") : emailLoginStep === "email" ? t("login.receive") : t("login.validate")}
                </button>
              </form>
              {emailLoginStep === "code" && (
                <button className="login-resend" type="button" disabled={isBusy} onClick={() => void handleResendCode()}>
                  {isBusy ? t("login.wait") : t("login.resend")}
                </button>
              )}
              <button className="login-step-back" type="button" disabled={isBusy} onClick={() => {
                setNotice("");
                setCode("");
                setEmailLoginStep(emailLoginStep === "code" ? "email" : "initial");
              }}>
                {t(emailLoginStep === "code" ? "login.useOther" : "login.back")}
              </button>
            </div>
          )}

          {notice && (
            <div className="login-notice-slot">
              <p className="login-notice" role="status">{t(notice)}</p>
            </div>
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
              {t("login.privacy")}
            </p>
          </div>

        </section>
      </div>
    </div>
  );
}
