import sys
import os
from mangum import Mangum

# Asegurar que la raíz del proyecto esté en sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.main import app

# Configuración de Mangum sin api_gateway_base_path y con lifespan off
handler = Mangum(app, lifespan="off")
__all__ = ["app", "handler"]
