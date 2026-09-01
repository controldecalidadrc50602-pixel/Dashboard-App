import sys
import os

# Asegurar que la raíz del proyecto esté en sys.path para Vercel Serverless
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.main import app

# Exponer tanto 'app' como 'handler' para máxima compatibilidad con Vercel Python Runtime
handler = app
__all__ = ["app", "handler"]
