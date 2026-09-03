from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

class BaseParser(ABC):
    """Clase base abstracta para todos los parsers de archivos fuente."""
    
    PARSER_VERSION = "base-v1.0"

    @abstractmethod
    def parse_row(
        self,
        row: List[str],
        headers: List[str],
        row_number: int
    ) -> Dict[str, Any]:
        """
        Procesa una fila cruda y retorna un diccionario con los datos normalizados,
        preservando trazabilidad, calidad y nulos explícitos.
        """
        pass

    @staticmethod
    def clean_str(val: Optional[str]) -> Optional[str]:
        """Limpia cadenas de texto. Si el valor es vacío, 'n/a', '-', o None, retorna None."""
        if val is None:
            return None
        s = str(val).strip()
        if not s or s.lower() in ["n/a", "na", "null", "-", "none"]:
            return None
        return s

    @staticmethod
    def parse_int(val: Optional[str]) -> Optional[int]:
        """Convierte a entero seguro. Retorna None si es inválido o no disponible (NUNCA 0 por defecto)."""
        s = BaseParser.clean_str(val)
        if s is None:
            return None
        try:
            # Eliminar posibles flotantes formateados como string "5.0"
            return int(float(s))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def parse_float(val: Optional[str]) -> Optional[float]:
        """Convierte a flotante seguro. Retorna None si es inválido o no disponible."""
        s = BaseParser.clean_str(val)
        if s is None:
            return None
        try:
            return float(s.replace(",", "."))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def parse_bool(val: Optional[str]) -> Optional[bool]:
        """Convierte a booleano explícito. Retorna None si no se puede determinar (diferenciando de False)."""
        s = BaseParser.clean_str(val)
        if s is None:
            return None
        if s.lower() in ["true", "1", "si", "yes", "ververdadero", "t"]:
            return True
        if s.lower() in ["false", "0", "no", "falso", "f"]:
            return False
        return None

    @staticmethod
    def parse_duration_seconds(val: Optional[str]) -> Optional[float]:
        """
        Normaliza duraciones como '12s', '01:30', '1m 20s' o '90' a segundos numéricos.
        """
        s = BaseParser.clean_str(val)
        if s is None:
            return None

        # Ejemplo: "12s", "12 sec", "12"
        match_sec = re.match(r'^(\d+(?:\.\d+)?)\s*(?:s|sec|seg)?$', s, re.IGNORECASE)
        if match_sec:
            return float(match_sec.group(1))

        # Ejemplo: "1m 20s", "1m", "20s"
        match_min_sec = re.match(r'^(?:(\d+)\s*m(?:in)?)?\s*(?:(\d+(?:\.\d+)?)\s*s(?:ec|eg)?)?$', s, re.IGNORECASE)
        if match_min_sec and (match_min_sec.group(1) or match_min_sec.group(2)):
            mins = float(match_min_sec.group(1) or 0)
            secs = float(match_min_sec.group(2) or 0)
            return mins * 60 + secs

        # Ejemplo: "MM:SS" o "HH:MM:SS"
        parts = s.split(":")
        if len(parts) == 2:
            try:
                return float(parts[0]) * 60 + float(parts[1])
            except ValueError:
                return None
        elif len(parts) == 3:
            try:
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            except ValueError:
                return None

        return None

    @staticmethod
    def parse_datetime(val: Optional[str]) -> Optional[datetime]:
        """
        Parsea fechas en diversos formatos comunes de Botmaker / Yeastar.
        Preserva la fecha/hora o retorna None si no es válida.
        """
        s = BaseParser.clean_str(val)
        if s is None:
            return None

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y"
        ]

        for fmt in formats:
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue

        return None
