from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.database import get_db
from app.routers.auth import get_current_admin
from app.schemas import ReportImportOut
from app.audit import log_audit_action

from app.services.connectors.botmaker_connector import BotmakerConnector
from app.services.connectors.yeastar_connector import YeastarConnector

router = APIRouter(prefix="/api/admin/connectors", tags=["connectors"])


@router.post("/botmaker/sync", response_model=ReportImportOut)
def sync_botmaker_api(
    client_id: int,
    period: str,
    request: Request,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Sincroniza métricas en vivo desde la API de Botmaker directamente al almacenamiento RAW."""
    connector = BotmakerConnector(access_token=token)
    try:
        import_rec = connector.sync_client_data(db, client_id, period)
        log_audit_action(
            db,
            username=admin.get("sub", "admin"),
            action="API_SYNC_BOTMAKER",
            resource_type="report_import",
            resource_id=str(import_rec.id),
            details={"client_id": client_id, "period": period, "filename": import_rec.original_filename},
            ip_address=request.client.host if request.client else None
        )
        return import_rec
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sincronizando Botmaker API: {str(e)}")


@router.post("/yeastar/sync", response_model=ReportImportOut)
def sync_yeastar_api(
    client_id: int,
    period: str,
    request: Request,
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Sincroniza métricas de llamadas y colas desde la Open API de Yeastar PBX Cloud."""
    connector = YeastarConnector(app_id=app_id, app_secret=app_secret)
    try:
        import_rec = connector.sync_queue_performance(db, client_id, period)
        log_audit_action(
            db,
            username=admin.get("sub", "admin"),
            action="API_SYNC_YEASTAR",
            resource_type="report_import",
            resource_id=str(import_rec.id),
            details={"client_id": client_id, "period": period, "filename": import_rec.original_filename},
            ip_address=request.client.host if request.client else None
        )
        return import_rec
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sincronizando Yeastar API: {str(e)}")


@router.get("/status")
def get_connectors_status(_=Depends(get_current_admin)):
    """Consulta el estado operativo de los conectores directos."""
    return {
        "botmaker_connector": {
            "status": "ONLINE",
            "supported_endpoints": ["/users", "/operatorsSessionsDebug", "/sessionStartingCauses"],
            "auth_type": "Bearer Token"
        },
        "yeastar_connector": {
            "status": "ONLINE",
            "supported_endpoints": ["Extension Statistics", "Extension Call Activity", "Queue Performance"],
            "auth_type": "App ID / App Secret"
        }
    }
