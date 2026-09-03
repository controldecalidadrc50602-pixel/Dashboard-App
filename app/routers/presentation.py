from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_username
from app.models import Client, MonthlyReport, ReportQualitativeAnalysis
from app.services.presentation_service import generate_pptx_presentation

router = APIRouter(prefix="/api/admin/clients", tags=["presentation"])

class PresentationRequest(BaseModel):
    period: str = "2026-09"
    theme: str = "teal"
    num_slides: int = 5
    sections: Optional[List[str]] = ["resumen", "eficiencia", "qualitative"]

@router.post("/{client_id}/presentation")
def create_client_presentation(
    client_id: int,
    body: PresentationRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_user)
):
    """
    Genera y descarga directamente una presentación PowerPoint (PPTX) determinística
    construida en memoria sin guardar archivos en disco.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Extraer mes/año del período YYYY-MM
    try:
        parts = body.period.split("-")
        year, month = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        year, month = 2026, 9

    # Buscar reporte cuantitativo
    report = db.query(MonthlyReport).filter(
        MonthlyReport.client_id == client_id,
        MonthlyReport.year == year,
        MonthlyReport.month == month
    ).first()

    kpi_metrics = {
        "chats": report.chats if report else 0,
        "support": report.support if report else 0,
        "leads": report.leads if report else 0,
        "sales": report.sales if report else 0,
        "csat": report.csat if report else 4.5
    }

    botmaker_data = (report.extra_data or {}).get("botmaker", {}) if report else {}

    # Buscar análisis cualitativo
    qual = db.query(ReportQualitativeAnalysis).filter(
        ReportQualitativeAnalysis.client_id == client_id,
        ReportQualitativeAnalysis.period == body.period
    ).first()

    qualitative_data = {
        "critical_points": qual.critical_points if qual else None,
        "warnings": qual.warnings if qual else None,
        "achievements": qual.achievements if qual else None,
        "general_info": qual.general_info if qual else None
    }

    stream = generate_pptx_presentation(
        client_name=client.name,
        period=body.period,
        theme=body.theme,
        num_slides=body.num_slides,
        sections=body.sections,
        kpi_metrics=kpi_metrics,
        qualitative_data=qualitative_data,
        botmaker_data=botmaker_data
    )

    clean_client_name = "".join(c for c in client.name if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
    filename = f"Reporte_{clean_client_name}_{body.period}.pptx"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers=headers
    )
