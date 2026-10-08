from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user
from app.api.params import RegionalCodePath
from app.models.identity import User
from app.schemas.organization import (
    OrganizationRegionalsResponse,
    OrganizationServiceCentersResponse,
)
from app.services.organization_catalog import organization_catalog_service


router = APIRouter(prefix="/api/organization", tags=["organization"])


@router.get("/regionals", response_model=OrganizationRegionalsResponse)
def read_regionals(_user: User = Depends(get_current_user)):
    return {
        "regionals": [
            {"code": regional.code, "label": regional.display_name or regional.code}
            for regional in organization_catalog_service.get_regional_sc_catalog()
        ]
    }


@router.get(
    "/regionals/{regional_code:path}/scs",
    response_model=OrganizationServiceCentersResponse,
)
def read_service_centers(regional_code: RegionalCodePath, _user: User = Depends(get_current_user)):
    service_centers = organization_catalog_service.get_service_centers(regional_code)
    if service_centers is None:
        raise HTTPException(status_code=404, detail="REGIONAL_NOT_FOUND")
    return {
        "regional_code": regional_code,
        "service_centers": [
            {
                "code": service_center.code,
                "name": service_center.name,
                "display_name": service_center.display_name,
            }
            for service_center in service_centers
        ],
    }
