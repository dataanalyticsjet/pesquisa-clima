from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceCenter:
    code: str
    name: str

    @property
    def display_name(self) -> str:
        return f"{self.code} — {self.name}"


@dataclass(frozen=True)
class RegionalCatalogEntry:
    code: str
    service_centers: tuple[ServiceCenter, ...]


# Approved partial catalog for management reporting. It intentionally contains
# no CNPJ and is not yet used to validate collaborator survey submissions.
REGIONAL_SC_CATALOG: tuple[RegionalCatalogEntry, ...] = (
    RegionalCatalogEntry(
        "BA",
        (
            ServiceCenter("AJU", "SE - ARACAJU"),
            ServiceCenter("FEC", "BA - FEIRA DE SANTANA"),
            ServiceCenter("VDC", "BA - VITORIA DA CONQUISTA"),
        ),
    ),
    RegionalCatalogEntry(
        "CE",
        (
            ServiceCenter("FOR", "CE - FORTALEZA"),
            ServiceCenter("JGS", "PE - JABOATÃO DOS GUARARAPES"),
            ServiceCenter("THE", "PI - TERESINA"),
        ),
    ),
    RegionalCatalogEntry(
        "GP",
        (
            ServiceCenter("ANA", "PA - ANANINDEUA"),
            ServiceCenter("BSB", "DF - SANTA MARIA"),
            ServiceCenter("CGB", "MT - CUIABA"),
            ServiceCenter("CGR", "MS - CAMPO GRANDE"),
            ServiceCenter("GYN", "GO - GOIANIA"),
            ServiceCenter("MRB", "PA - MARABÁ"),
            ServiceCenter("PMW", "TO - PALMAS"),
            ServiceCenter("PVH", "RO - NOVO PORTO VELHO"),
            ServiceCenter("STM", "PA - SANTARÉM"),
        ),
    ),
    RegionalCatalogEntry(
        "MG/SPN",
        (
            ServiceCenter("CGE", "MG - CONTAGEM"),
            ServiceCenter("CVH", "MG - CONSELHEIRO LAFAIETE"),
            ServiceCenter("RAO", "SP - RIBEIRÃO PRETO"),
            ServiceCenter("RBP", "SP - RIBEIRÃO PRETO"),
        ),
    ),
    RegionalCatalogEntry(
        "PR",
        (
            ServiceCenter("BNU", "SC - BLUMENAU"),
            ServiceCenter("NSR", "RS - NOVA SANTA RITA"),
            ServiceCenter("SJS", "PR - SÃO JOSÉ DOS PINHAIS"),
        ),
    ),
    RegionalCatalogEntry(
        "RJ",
        (
            ServiceCenter("SJM", "RJ - SÃO JOÃO DO MERITI"),
            ServiceCenter("SRR-ES", "ES - SERRA"),
        ),
    ),
    RegionalCatalogEntry("SPE", (ServiceCenter("GRU", "SP - GUARULHOS"),)),
    RegionalCatalogEntry("SPS", (ServiceCenter("BRE", "SP - BARUERI"),)),
)


class OrganizationCatalogService:
    """Catalog adapter for the approved partial management reporting source.

    The partial Regional/SC catalog is not a complete organizational catalog,
    so selection validation stays unavailable until the complete official
    source (including CNPJ) is approved.
    """

    def get_regional_sc_catalog(self) -> tuple[RegionalCatalogEntry, ...]:
        """Return the approved partial Regional/SC list for management views."""
        return REGIONAL_SC_CATALOG

    def validate_selection(
        self,
        option_source: str,
        option_code: str,
        *,
        regional_code: str | None = None,
        base_code: str | None = None,
    ) -> bool | None:
        return None


organization_catalog_service = OrganizationCatalogService()
