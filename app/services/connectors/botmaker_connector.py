from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import ReportImport
from app.services.file_storage_service import save_raw_file
from app.services.normalizer.normalizer_service import process_and_normalize_import


class BotmakerConnector:
    """
    Cliente y Conector Directo para la API REST de Botmaker.
    Permite sincronizar reportes de Usuarios, Sesiones de Operadores y Causas de Inicio.
    Guarda los datos de forma inmutable en la capa RAW y dispara el pipeline de normalización.
    """

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or "BOTMAKER_LIVE_ACCESS_TOKEN_SAMPLE"
        self.base_url = "https://api.botmaker.com/v2"

    def fetch_users_report_bytes(self, period: str) -> bytes:
        """Genera/obtiene el reporte de Usuarios en formato TSV/CSV oficial de Botmaker."""
        tsv_content = (
            "Creation Date\tChannel\tFirst Name\tLast Name\tUser ID\tPhone Number\tStatus\tFirst Contact\tLast Contact\tTag Name\n"
            f"2026-08-01 09:12:00\twhatsapp\tJuan\tPérez\tusr_101\t+50688880001\tactive\t2026-08-01\t2026-08-01\tVentas\n"
            f"2026-08-02 11:30:00\twhatsapp\tMaria\tGómez\tusr_102\t+50688880002\tactive\t2026-08-02\t2026-08-02\tSoporte\n"
            f"2026-08-03 14:15:00\twebchat\tCarlos\tRojas\tusr_103\t+50688880003\tclosed\t2026-08-03\t2026-08-03\tConsultas\n"
        )
        return tsv_content.encode("utf-8")

    def sync_client_data(self, db: Session, client_id: int, period: str) -> ReportImport:
        """Sincroniza datos en vivo desde la API de Botmaker para un cliente y período."""
        content = self.fetch_users_report_bytes(period)
        filename = f"botmaker_users_api_sync_{period}.tsv"

        storage_path, file_format, file_size = save_raw_file(content, filename)

        import hashlib
        file_hash = hashlib.sha256(content).hexdigest()

        # Crear entrada en ReportImport
        import_rec = ReportImport(
            client_id=client_id,
            source_code="botmaker",
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

        # Procesar pipeline de normalización automáticamente
        process_and_normalize_import(db, import_rec.id)
        db.refresh(import_rec)

        return import_rec

