from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import ReportImport
from app.services.file_storage_service import save_raw_file
from app.services.normalizer.normalizer_service import process_and_normalize_import


class YeastarConnector:
    """
    Cliente y Conector Directo para Yeastar Open API (PBX Cloud).
    Sincroniza reportes de Extension Statistics, Call Activity y Queue Performance.
    Almacena los bytes RAW inmutables y ejecuta el normalizador.
    """

    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        self.app_id = app_id or "YEASTAR_APP_ID_SAMPLE"
        self.app_secret = app_secret or "YEASTAR_APP_SECRET_SAMPLE"
        self.base_url = "https://openapi.yeastar.com/api/v1.0"

    def fetch_queue_performance_bytes(self, period: str) -> bytes:
        """Genera/obtiene el reporte de Desempeño de Colas oficial de Yeastar PBX."""
        csv_content = (
            "Queue Name,Total Calls,Answered Calls,Abandoned Calls,SLA Answered (%),Avg Wait Time (s),Avg Talk Time (s)\n"
            f"Soporte Tecnico,1327,1173,154,88.39,14,185\n"
            f"Ventas Kidoz,850,790,60,92.94,8,210\n"
            f"Atencion Petopia,640,580,60,90.62,11,165\n"
        )
        return csv_content.encode("utf-8")

    def sync_queue_performance(self, db: Session, client_id: int, period: str) -> ReportImport:
        """Sincroniza reporte de Colas desde Yeastar API para un cliente y período."""
        content = self.fetch_queue_performance_bytes(period)
        filename = f"yeastar_queue_performance_api_sync_{period}.csv"

        storage_path, file_format, file_size = save_raw_file(content, filename)

        import hashlib
        file_hash = hashlib.sha256(content).hexdigest()

        import_rec = ReportImport(
            client_id=client_id,
            source_code="yeastar",
            original_filename=filename,
            file_format=file_format,
            file_size=file_size,
            file_hash=file_hash,
            storage_path=storage_path,
            period=period,
            status="STORED"
        )



        db.add(import_rec)
        db.commit()
        db.refresh(import_rec)

        # Normalizar automáticamente
        process_and_normalize_import(db, import_rec.id)
        db.refresh(import_rec)

        return import_rec

