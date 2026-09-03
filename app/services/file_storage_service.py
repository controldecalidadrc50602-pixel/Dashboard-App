import os
import uuid
import tempfile
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def get_storage_dir() -> str:
    """Determina dinámicamente un directorio escribible para almacenamiento inmutable RAW."""
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        path = os.path.join("/tmp", "uploads", "raw")
    else:
        path = os.path.join(os.getcwd(), "uploads", "raw")
    
    try:
        os.makedirs(path, exist_ok=True)
        test_file = os.path.join(path, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return path
    except Exception as e:
        logger.warning(f"Directorio {path} no es escribible ({e}). Usando directorio temporal fallback.")
        tmp_path = os.path.join(tempfile.gettempdir(), "uploads", "raw")
        os.makedirs(tmp_path, exist_ok=True)
        return tmp_path


MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {".tsv", ".csv", ".xlsx", ".xls", ".txt", ".json", ".md"}
DANGEROUS_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bat", ".cmd", ".sh", ".py", ".pyc",
    ".js", ".vbs", ".php", ".asp", ".aspx", ".jsp", ".cgi", ".pl", ".rb", ".ps1"
}


def ensure_raw_storage_dir() -> str:
    """Garantiza la existencia del directorio seguro uploads/raw/."""
    return get_storage_dir()


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
    raw_dir = ensure_raw_storage_dir()
    
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE_BYTES // (1024*1024)} MB")

    _, ext = os.path.splitext(original_filename.lower())
    ext = ext if ext else ".txt"
    file_format = ext.lstrip(".")

    if not is_extension_allowed(original_filename):
        raise ValueError(f"Extensión de archivo no permitida o riesgosa: '{ext}'")

    internal_filename = f"{uuid.uuid4()}{ext}"
    storage_path = os.path.join(raw_dir, internal_filename)

    with open(storage_path, "wb") as f:
        f.write(content)

    return storage_path, file_format, len(content)


def read_raw_file(storage_path: str) -> bytes:
    """Lee de forma inmutable el contenido RAW almacenado."""
    if not os.path.exists(storage_path):
        raise FileNotFoundError("El archivo almacenado no fue encontrado en el disco.")
    with open(storage_path, "rb") as f:
        return f.read()
