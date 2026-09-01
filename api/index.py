import sys
import os

# Añadir el directorio raíz a sys.path para que Python pueda importar el módulo 'app' en Vercel Serverless
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.main import app

# Vercel Serverless Function Handler
__all__ = ["app"]
