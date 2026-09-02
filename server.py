import sys
import os
from mangum import Mangum

root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.main import app

handler = Mangum(app, lifespan="off")
__all__ = ["app", "handler"]
