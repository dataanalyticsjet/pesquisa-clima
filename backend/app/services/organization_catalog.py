class OrganizationCatalogService:
    """Adapter boundary for the future official organizational catalog.

    Returning None means no official source is configured. Production data is
    intentionally absent until an authoritative source is approved.
    """

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
