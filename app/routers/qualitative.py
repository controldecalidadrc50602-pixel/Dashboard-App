from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models import Client, ReportQualitativeAnalysis, User
from app.schemas import QualitativeAnalysisCreate, QualitativeAnalysisUpdate, QualitativeAnalysisOut
from app.dependencies import get_current_user, require_superadmin, get_username
from app.audit import log_audit_action

router = APIRouter(prefix="/api/admin/clients", tags=["qualitative"])


@router.get("/{client_id}/qualitative/{period}", response_model=QualitativeAnalysisOut)
def get_qualitative_analysis(
    client_id: int,
    period: str,
    db: Session = Depends(get_db),
    _ = Depends(get_current_user)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    qa = db.query(ReportQualitativeAnalysis).filter(
        ReportQualitativeAnalysis.client_id == client_id,
        ReportQualitativeAnalysis.period == period
    ).first()

    if not qa:
        # Retornar objeto estructural por defecto para períodos sin análisis guardado
        return ReportQualitativeAnalysis(
            id=0,
            client_id=client_id,
            period=period,
            critical_points="",
            warnings="",
            achievements="",
            general_info="",
            created_by=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    return qa


@router.post("/{client_id}/qualitative/{period}", response_model=QualitativeAnalysisOut, status_code=201)
def create_qualitative_analysis(
    client_id: int,
    period: str,
    body: QualitativeAnalysisCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_superadmin)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    existing = db.query(ReportQualitativeAnalysis).filter(
        ReportQualitativeAnalysis.client_id == client_id,
        ReportQualitativeAnalysis.period == period
    ).first()

    username = get_username(admin)

    if existing:
        # Si ya existe, realizar actualización (upsert transparente)
        existing.critical_points = body.critical_points
        existing.warnings = body.warnings
        existing.achievements = body.achievements
        existing.general_info = body.general_info
        existing.created_by = username
        existing.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(existing)

        log_audit_action(
            db,
            username=username,
            action="UPDATE_QUALITATIVE_ANALYSIS",
            resource_type="qualitative_analysis",
            resource_id=str(existing.id),
            details={"client_id": client_id, "period": period}
        )
        return existing

    qa = ReportQualitativeAnalysis(
        client_id=client_id,
        period=period,
        critical_points=body.critical_points,
        warnings=body.warnings,
        achievements=body.achievements,
        general_info=body.general_info,
        created_by=username
    )

    db.add(qa)
    db.commit()
    db.refresh(qa)

    log_audit_action(
        db,
        username=username,
        action="CREATE_QUALITATIVE_ANALYSIS",
        resource_type="qualitative_analysis",
        resource_id=str(qa.id),
        details={"client_id": client_id, "period": period}
    )

    return qa


@router.put("/{client_id}/qualitative/{period}", response_model=QualitativeAnalysisOut)
def update_qualitative_analysis(
    client_id: int,
    period: str,
    body: QualitativeAnalysisUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_superadmin)
):
    # Delega en la lógica de upsert transparente
    return create_qualitative_analysis(
        client_id=client_id,
        period=period,
        body=QualitativeAnalysisCreate(**body.model_dump()),
        db=db,
        admin=admin
    )
