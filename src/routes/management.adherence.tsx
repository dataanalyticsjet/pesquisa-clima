import { createFileRoute } from "@tanstack/react-router";
import { ManagementLayout, ManagementPageTitle } from "../components/management/ManagementNav";
import { useI18n } from "../i18n/context";

export const Route = createFileRoute("/management/adherence")({ component: ManagementAdherence });

function ManagementAdherence() {
  const { t } = useI18n();
  return (
    <ManagementLayout>
      <ManagementPageTitle title={t("management.adherenceTitle")} description={t("management.adherenceDescription")} />
      <div className="management-pillars-state" role="status">
        <span>
          <strong>{t("management.adherenceUnavailable")}</strong><br />
          {t("management.populationMissing")}
        </span>
      </div>
    </ManagementLayout>
  );
}
