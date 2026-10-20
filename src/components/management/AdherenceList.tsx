import { useI18n } from "../../i18n/context";
import type { ManagementAdherenceRegional } from "../../services/management";

export function AdherenceList({ regionals }: { regionals: ManagementAdherenceRegional[] }) {
  const { locale, t } = useI18n();
  const formatInteger = new Intl.NumberFormat(locale === "zh" ? "zh-CN" : "pt-BR");
  const maxVisibleRegionalCount = Math.max(
    0,
    ...regionals.map((regional) => regional.response_count ?? 0),
  );

  return (
    <ul className="adherence-list">
      {regionals.map((regional) => {
        const maxVisibleBaseCount = Math.max(
          0,
          ...regional.bases.map((base) => base.response_count ?? 0),
        );
        return (
          <li className="adherence-group" key={regional.regional_code}>
            <details className="adherence-group__details" open>
              <summary className="adherence-row">
                <span className="adherence-row__region">{regional.regional_name}</span>
                <div className="adherence-row__track" aria-hidden="true">
                  <span
                    style={{
                      width: maxVisibleRegionalCount === 0
                        ? "0%"
                        : `${(regional.response_count / maxVisibleRegionalCount) * 100}%`,
                    }}
                  />
                </div>
                <strong>{formatInteger.format(regional.response_count)}</strong>
                <span className="adherence-row__disclosure" aria-hidden="true" />
              </summary>
              <ul
                className="adherence-base-list"
                aria-label={t("management.adherenceBasesAria", { code: regional.regional_code })}
              >
                {regional.bases.map((base) => (
                  <li className="adherence-base-row" key={base.base_code}>
                    <span className="adherence-base-row__code">{base.base_code}</span>
                    <span className="adherence-base-row__name">{base.base_name}</span>
                    <div className="adherence-base-row__track" aria-hidden="true">
                      <span
                        style={{
                          width: maxVisibleBaseCount === 0
                            ? "0%"
                            : `${(base.response_count / maxVisibleBaseCount) * 100}%`,
                        }}
                      />
                    </div>
                    <strong>{formatInteger.format(base.response_count)}</strong>
                  </li>
                ))}
              </ul>
            </details>
          </li>
        );
      })}
    </ul>
  );
}
