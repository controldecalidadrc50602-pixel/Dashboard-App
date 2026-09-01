import hashlib
from sqlalchemy.orm import Session
from app.models import ReportImport
from typing import Optional, Tuple

def calculate_sha256(content: bytes) -> str:
    """Calcula el hash criptográfico SHA-256 en formato Hexadecimal (64 caracteres)."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()


def check_duplicate_import(db: Session, file_hash: str, client_id: int) -> Tuple[bool, Optional[ReportImport]]:
    """
    Verifica si un archivo con el mismo hash SHA-256 ya ha sido importado para el cliente.
    Retorna (es_duplicado, objeto_import_existente).
    """
    existing = db.query(ReportImport).filter(
        ReportImport.file_hash == file_hash,
        ReportImport.client_id == client_id,
        ReportImport.status != "INVALID"
    ).first()
    
    if existing:
        return True, existing
    return False, None
