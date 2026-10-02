from pydantic import BaseModel, ConfigDict


class OrganizationRegionalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    label: str


class OrganizationRegionalsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    regionals: list[OrganizationRegionalResponse]


class OrganizationServiceCenterResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    display_name: str


class OrganizationServiceCentersResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    regional_code: str
    service_centers: list[OrganizationServiceCenterResponse]
