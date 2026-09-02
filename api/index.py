import sys
import os
from mangum import Mangum

# Asegurar que la raíz del proyecto esté en sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.main import app

# Mangum adapta FastAPI (ASGI) a Vercel/AWS Lambda HTTP Events resolviendo el 404 Not Found
handler = Mangum(app, api_gateway_base_path="")
__all__ = ["app", "handler"]
