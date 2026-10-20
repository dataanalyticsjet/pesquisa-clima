import { useI18n } from "../../i18n/context";
import type { ManagementAdherenceRegional } from "../../services/management";

export function AdherenceList({ regionals }: { regionals: ManagementAdherenceRegional[] }) {
  const { locale, t } = useI18n();
  const formatInteger = new Intl.NumberFormat(locale === "zh" ? "zh-CN" : "pt-BR");
  const maxVisibleCount = Math.max(
    0,
    ...regionals.map((regional) => regional.response_count ?? 0),
  );

  return (
    <ul className="adherence-list">
      {regionals.map(({ regional_code, response_count }) => (
        <li className="adherence-row" key={regional_code}>
          <span className="adherence-row__region">{regional_code}</span>
          {response_count === null ? (
            <span className="adherence-row__protected" role="status">{t("management.insufficient")}</span>
          ) : (
            <>
              <div className="adherence-row__track" aria-hidden="true">
                <span
                  style={{
                    width: maxVisibleCount === 0
                      ? "0%"
                      : `${(response_count / maxVisibleCount) * 100}%`,
                  }}
                />
              </div>
              <strong>{formatInteger.format(response_count)}</strong>
            </>
          )}
        </li>
      ))}
    </ul>
  );
}
