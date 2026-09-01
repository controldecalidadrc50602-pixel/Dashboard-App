import os
import uuid
from typing import Tuple

if os.getenv("VERCEL"):
    RAW_STORAGE_DIR = os.path.join("/tmp", "uploads", "raw")
else:
    RAW_STORAGE_DIR = os.path.join(os.getcwd(), "uploads", "raw")

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {".tsv", ".csv", ".xlsx", ".xls", ".txt", ".json", ".md"}
DANGEROUS_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bat", ".cmd", ".sh", ".py", ".pyc",
    ".js", ".vbs", ".php", ".asp", ".aspx", ".jsp", ".cgi", ".pl", ".rb", ".ps1"
}


def ensure_raw_storage_dir():
    """Garantiza la existencia del directorio seguro uploads/raw/."""
    os.makedirs(RAW_STORAGE_DIR, exist_ok=True)


def is_extension_allowed(filename: str) -> bool:
    """Valida si la extensión del archivo es permitida y segura."""
    _, ext = os.path.splitext(filename.lower())
    if ext in DANGEROUS_EXTENSIONS:
        return False
    return ext in ALLOWED_EXTENSIONS or ext == ""


def save_raw_file(content: bytes, original_filename: str) -> Tuple[str, str, int]:
    """
    Guarda inmutablemente los bytes del archivo original en uploads/raw/ usando un identificador UUID interno.
    Retorna (storage_path, file_format, file_size).
    """
    ensure_raw_storage_dir()
    
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE_BYTES // (1024*1024)} MB")

    _, ext = os.path.splitext(original_filename.lower())
    ext = ext if ext else ".txt"
    file_format = ext.lstrip(".")

    if not is_extension_allowed(original_filename):
        raise ValueError(f"Extensión de archivo no permitida o riesgosa: '{ext}'")

    internal_filename = f"{uuid.uuid4()}{ext}"
    storage_path = os.path.join(RAW_STORAGE_DIR, internal_filename)

    with open(storage_path, "wb") as f:
        f.write(content)

    return storage_path, file_format, len(content)


def read_raw_file(storage_path: str) -> bytes:
    """Lee de forma inmutable el contenido RAW almacenado."""
    if not os.path.exists(storage_path):
        raise FileNotFoundError("El archivo almacenado no fue encontrado en el disco.")
    with open(storage_path, "rb") as f:
        return f.read()
