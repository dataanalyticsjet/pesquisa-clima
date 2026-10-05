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
    display_name: str | None = None


# Approved Regional → SC catalog shared by survey selection and management reporting.
# Q03 work-profile choices are static survey options and do not belong in this catalog.
REGIONAL_SC_CATALOG: tuple[RegionalCatalogEntry, ...] = (
    RegionalCatalogEntry(
        "MATRIZ",
        (ServiceCenter("MATRIZ", "Matriz"),),
        display_name="Matriz",
    ),
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
    """Read and validate the approved Regional → SC catalog."""

    def get_regional_sc_catalog(self) -> tuple[RegionalCatalogEntry, ...]:
        """Return the single approved Regional/SC source for all frontend consumers."""
        return REGIONAL_SC_CATALOG

    def get_regionals(self) -> tuple[str, ...]:
        return tuple(regional.code for regional in REGIONAL_SC_CATALOG)

    def get_service_centers(self, regional_code: str) -> tuple[ServiceCenter, ...] | None:
        regional = next(
            (entry for entry in REGIONAL_SC_CATALOG if entry.code == regional_code),
            None,
        )
        return None if regional is None else regional.service_centers

    def validate_selection(
        self,
        option_source: str,
        option_code: str,
        *,
        regional_code: str | None = None,
        base_code: str | None = None,
    ) -> bool:
        if option_source == "ORG_REGIONAL":
            return option_code in self.get_regionals()

        if option_source == "ORG_BASE":
            if regional_code is None:
                return False
            service_centers = self.get_service_centers(regional_code)
            return service_centers is not None and any(
                service_center.code == option_code for service_center in service_centers
            )

        # Legacy CNPJ option sources are unsupported; current Q03 uses static profile choices.
        return False


organization_catalog_service = OrganizationCatalogService()
