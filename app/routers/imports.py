from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import csv

from app.database import get_db
from app.models import Client, ReportImport, User
from app.schemas import ReportImportOut, ReportImportPreview
from app.dependencies import get_current_user, get_username
from app.audit import log_audit_action

from app.services.hash_service import calculate_sha256, check_duplicate_import
from app.services.file_storage_service import save_raw_file, read_raw_file
from app.services.detector_service import analyze_file_content
from app.services.validator_service import validate_import_structure

router = APIRouter(prefix="/api/admin/imports", tags=["imports"])


@router.post("/", response_model=ReportImportOut, status_code=201)
async def upload_and_import_file(
    request: Request,
    file: UploadFile = File(...),
    client_id: int = Form(...),
    source_code: str = Form(...),
    report_type: Optional[str] = Form(None),
    period: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_user)
):
    # 1. Verificar existencia del cliente
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    content = await file.read()
    filename = file.filename or "report_file.txt"

    # 2. Calcular hash SHA-256 e inspeccionar idempotencia
    file_hash = calculate_sha256(content)
    is_duplicate, existing_import = check_duplicate_import(db, file_hash, client_id)

    log_audit_action(
        db,
        username=get_username(admin),
        action="IMPORT_STARTED",
        resource_type="import",
        details={"filename": filename, "client_id": client_id, "file_hash": file_hash},
        ip_address=request.client.host if request.client else None
    )

    if is_duplicate and existing_import:
        dup_import = ReportImport(
            client_id=client_id,
            source_code=source_code,
            report_type=report_type or existing_import.report_type,
            period=period or existing_import.period,
            original_filename=filename,
            storage_path=existing_import.storage_path,
            file_format=existing_import.file_format,
            file_size=len(content),
            file_hash=file_hash,
            status="DUPLICATE",
            records_count=existing_import.records_count,
            warnings=[{"row": 0, "field": "hash", "message": f"Archivo idéntico al previamente cargado (Import ID {existing_import.id}).", "severity": "WARNING"}],
            errors=[],
            metadata_info=existing_import.metadata_info,
            uploaded_by=get_username(admin)
        )
        db.add(dup_import)
        db.commit()
        db.refresh(dup_import)

        log_audit_action(
            db,
            username=get_username(admin),
            action="IMPORT_DUPLICATE",
            resource_type="import",
            resource_id=str(dup_import.id),
            details={"original_import_id": existing_import.id}
        )

        res = ReportImportOut.model_validate(dup_import)
        res.client_name = client.name
        return res

    # 3. Guardar archivo RAW inmutable en uploads/raw/
    try:
        storage_path, file_format, file_size = save_raw_file(content, filename)
    except ValueError as val_err:
        log_audit_action(
            db,
            username=get_username(admin),
            action="IMPORT_FAILED",
            resource_type="import",
            details={"reason": str(val_err)}
        )
        raise HTTPException(status_code=400, detail=str(val_err))

    # 4. Analizar contenido del archivo (Encoding, delimitador, filas)
    analysis = analyze_file_content(content, filename)
    final_period = period if period and period != "requiere_confirmacion" else analysis["period"]

    # Re-obtener todas las filas para la etapa de validación estructurada
    all_rows = []
    if file_format in ["csv", "tsv", "txt"]:
        enc = analysis.get("encoding", "utf-8")
        delim = analysis.get("delimiter", "\t")
        if delim == "\\t":
            delim = "\t"
        text = content.decode(enc, errors="replace")
        reader = csv.reader([l for l in text.splitlines() if l.strip()], delimiter=delim)
        all_rows = list(reader)
    elif file_format in ["xlsx", "xls"]:
        all_rows = [analysis.get("headers", [])] + analysis.get("sample_rows", [])

    # 5. Validar estructura por fila (Sin pérdida silenciosa de datos)
    rep_type_final = report_type or ("users" if "users" in filename.lower() else "operatorsSessionsDebug" if "operators" in filename.lower() else "sessionStartingCauses" if "session" in filename.lower() else "generic")
    status, warnings, errors = validate_import_structure(source_code, rep_type_final, analysis, all_rows)

    # 6. Registrar en Base de Datos
    import_obj = ReportImport(
        client_id=client_id,
        source_code=source_code,
        report_type=rep_type_final,
        period=final_period,
        original_filename=filename,
        storage_path=storage_path,
        file_format=file_format,
        file_size=file_size,
        file_hash=file_hash,
        status=status,
        records_count=analysis["total_rows"],
        warnings=warnings,
        errors=errors,
        metadata_info=analysis,
        uploaded_by=get_username(admin)
    )

    db.add(import_obj)
    db.commit()
    db.refresh(import_obj)

    log_audit_action(
        db,
        username=get_username(admin),
        action="IMPORT_COMPLETED" if status != "INVALID" else "IMPORT_FAILED",
        resource_type="import",
        resource_id=str(import_obj.id),
        details={"status": status, "records": analysis["total_rows"]}
    )

    res = ReportImportOut.model_validate(import_obj)
    res.client_name = client.name
    return res


@router.get("/", response_model=List[ReportImportOut])
def list_imports(
    client_id: Optional[int] = None,
    source_code: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    q = db.query(ReportImport)
    if client_id:
        q = q.filter(ReportImport.client_id == client_id)
    if source_code:
        q = q.filter(ReportImport.source_code == source_code)
    if status:
        q = q.filter(ReportImport.status == status)

    imports = q.order_by(ReportImport.created_at.desc()).all()
    results = []
    for imp in imports:
        item = ReportImportOut.model_validate(imp)
        item.client_name = imp.client.name if imp.client else "Desconocido"
        results.append(item)
    return results


@router.get("/{import_id}", response_model=ReportImportOut)
def get_import_detail(
    import_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    imp = db.query(ReportImport).filter(ReportImport.id == import_id).first()
    if not imp:
        raise HTTPException(status_code=404, detail="Importación no encontrada")
    res = ReportImportOut.model_validate(imp)
    res.client_name = imp.client.name if imp.client else "Desconocido"
    return res


@router.get("/{import_id}/preview", response_model=ReportImportPreview)
def get_import_preview(
    import_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_user)
):
    imp = db.query(ReportImport).filter(ReportImport.id == import_id).first()
    if not imp:
        raise HTTPException(status_code=404, detail="Importación no encontrada")

    # Registrar acceso a archivo RAW en log de auditoría
    log_audit_action(
        db,
        username=get_username(admin),
        action="RAW_FILE_ACCESSED",
        resource_type="import",
        resource_id=str(imp.id),
        ip_address=request.client.host if request.client else None
    )

    try:
        content = read_raw_file(imp.storage_path)
        analysis = analyze_file_content(content, imp.original_filename)
    except Exception as e:
        analysis = {
            "delimiter": "desconocido",
            "encoding": "desconocido",
            "headers": [],
            "sample_rows": [],
            "total_rows": imp.records_count
        }

    return ReportImportPreview(
        import_id=imp.id,
        original_filename=imp.original_filename,
        source_code=imp.source_code,
        client_name=imp.client.name if imp.client else "Desconocido",
        report_type=imp.report_type,
        period=imp.period or "requiere_confirmacion",
        file_hash=imp.file_hash,
        file_format=imp.file_format,
        file_size=imp.file_size,
        status=imp.status,
        delimiter=analysis.get("delimiter", "\t"),
        encoding=analysis.get("encoding", "utf-8"),
        headers=analysis.get("headers", []),
        sample_rows=analysis.get("sample_rows", []),
        total_rows=analysis.get("total_rows", imp.records_count),
        warnings=imp.warnings or [],
        errors=imp.errors or []
    )


# ──────────────────────────────────────────────
# Endpoints de Normalización & Métricas Base (Fase 03)
# ──────────────────────────────────────────────
from app.services.normalizer.normalizer_service import process_and_normalize_import
from app.services.normalizer.metrics_calculator_service import calculate_base_metrics
from app.models import NormalizedRecord


@router.post("/{import_id}/process")
def process_import_endpoint(
    import_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_user)
):
    """Ejecuta el parser específico y guarda los NormalizedRecords (Reprocesable)."""
    try:
        imp, summary = process_and_normalize_import(db, import_id)
        log_audit_action(
            db,
            username=get_username(admin),
            action="IMPORT_NORMALIZED",
            resource_type="import",
            resource_id=str(import_id),
            details=summary
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{import_id}/normalized-summary")
def get_normalized_summary_endpoint(
    import_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Devuelve el resumen de registros normalizados y métricas operativas base."""
    imp = db.query(ReportImport).filter(ReportImport.id == import_id).first()
    if not imp:
        raise HTTPException(status_code=404, detail="Importación no encontrada")

    metrics_data = calculate_base_metrics(db, import_id)
    return {
        "import_id": imp.id,
        "original_filename": imp.original_filename,
        "client_name": imp.client.name if imp.client else "Desconocido",
        "source_code": imp.source_code,
        "report_type": imp.report_type,
        "period": imp.period,
        "status": imp.status,
        "summary": metrics_data["summary"],
        "base_metrics": metrics_data["metrics"],
        "typifications_breakdown": metrics_data["typifications_breakdown"]
    }


@router.get("/{import_id}/quality")
def get_import_quality_endpoint(
    import_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Devuelve el reporte de calidad de datos, trazabilidad y estado por fila."""
    imp = db.query(ReportImport).filter(ReportImport.id == import_id).first()
    if not imp:
        raise HTTPException(status_code=404, detail="Importación no encontrada")

    records = db.query(NormalizedRecord).filter(NormalizedRecord.import_id == import_id).all()

    total_records = len(records)
    valid_count = sum(1 for r in records if r.quality_status == "VALID")
    warnings_count = sum(1 for r in records if r.quality_status == "VALID_WITH_WARNINGS")

    sample_traceability = []
    for r in records[:5]:
        sample_traceability.append({
            "record_id": r.id,
            "row_number": r.row_number,
            "parser_version": r.parser_version,
            "event_id": r.event_id,
            "user_id": r.user_id,
            "quality_status": r.quality_status,
            "raw_snippet": r.raw_data
        })

    return {
        "import_id": imp.id,
        "total_records": total_records,
        "valid_records": valid_count,
        "records_with_warnings": warnings_count,
        "sample_traceability": sample_traceability,
        "import_warnings": imp.warnings or [],
        "import_errors": imp.errors or []
    }

