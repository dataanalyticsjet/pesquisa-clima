from fastapi import APIRouter, HTTPException

from app.services.database_health import read_database_health


router = APIRouter(tags=["database"])


@router.get("/api/database/health")
def database_health():
    try:
        return read_database_health()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "message": "Database health check failed."},
        ) from None
