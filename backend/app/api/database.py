from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_admin_access
from app.models.identity import User

from app.services.database_health import read_database_health


router = APIRouter(tags=["database"])


@router.get("/api/database/health")
def database_health(_admin: User = Depends(require_admin_access)):
    try:
        return read_database_health()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "message": "Database health check failed."},
        ) from None
