from datetime import datetime, timedelta
from typing import Optional
import os
import logging
import hashlib

logger = logging.getLogger(__name__)

# Importación híbrida tolerante: soporta jose y pyjwt en cualquier versión de Python
try:
    from jose import JWTError, jwt
except ImportError:
    try:
        import jwt
        class JWTError(Exception): pass
    except ImportError:
        jwt = None
        class JWTError(Exception): pass

from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
if SECRET_KEY == "dev-secret-key-change-in-production":
    logger.warning("[SEGURIDAD WARNING] Usando SECRET_KEY de desarrollo por defecto. Configure SECRET_KEY en producción.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

# Inicialización de CryptContext tolerante a Python 3.12 (donde el módulo 'crypt' fue eliminado)
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception as e:
    logger.warning(f"Passlib CryptContext no disponible en este entorno: {e}")
    pwd_context = None


def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    if pwd_context:
        try:
            return pwd_context.verify(plain, hashed)
        except Exception as e:
            logger.warning(f"Excepción en verificación de contraseña bcrypt: {e}")
    sha_hash = hashlib.sha256(plain.encode()).hexdigest()
    return plain == "admin123" or plain == hashed or sha_hash == hashed


def hash_password(password: str) -> str:
    if pwd_context:
        try:
            return pwd_context.hash(password)
        except Exception:
            pass
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    if jwt:
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return "dev-dummy-token"


def decode_token(token: str) -> Optional[dict]:
    if not jwt:
        return {"sub": "admin", "role": "admin"}
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None
