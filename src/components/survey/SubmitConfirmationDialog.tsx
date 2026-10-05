import { useEffect, useRef } from "react";
import { useI18n } from "../../i18n/context";

type SubmitConfirmationDialogProps = {
  onCancel: () => void;
  onConfirm: () => void;
  isSubmitting?: boolean;
};

export function SubmitConfirmationDialog({ onCancel, onConfirm, isSubmitting = false }: SubmitConfirmationDialogProps) {
  const confirmButtonRef = useRef<HTMLButtonElement>(null);
  const { t } = useI18n();

  useEffect(() => {
    confirmButtonRef.current?.focus();
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isSubmitting) onCancel();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isSubmitting, onCancel]);

  return (
    <div className="survey-dialog-backdrop">
      <section
        aria-describedby="survey-confirm-description"
        aria-labelledby="survey-confirm-title"
        aria-modal="true"
        className="survey-dialog"
        role="dialog"
      >
        <span className="survey-dialog__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path d="M12 3.5 19 6v5.3c0 4.4-2.9 7.5-7 9.2-4.1-1.7-7-4.8-7-9.2V6l7-2.5Z" fill="none" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.6" />
            <path d="m9 12 2 2 4-4" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" />
          </svg>
        </span>
        <h2 id="survey-confirm-title">{t("survey.confirmTitle")}</h2>
        <p id="survey-confirm-description">{t("survey.confirmDescription")}</p>
        <div className="survey-dialog__actions">
          <button className="survey-button survey-button--secondary" disabled={isSubmitting} onClick={onCancel} type="button">
            {t("survey.back")}
          </button>
          <button className="survey-button survey-button--primary" disabled={isSubmitting} onClick={onConfirm} ref={confirmButtonRef} type="button">
            {isSubmitting ? t("survey.sending") : t("survey.confirm")}
          </button>
        </div>
      </section>
    </div>
  );
}
