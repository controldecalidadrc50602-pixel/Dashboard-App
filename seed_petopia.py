"""
Script para cargar los datos del cliente Petopia 2026.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, engine
from app.models import Base, Client, MonthlyReport

Base.metadata.create_all(bind=engine)
db = SessionLocal()

existing = db.query(Client).filter(Client.name == "Petopia").first()
if existing:
    print("[SKIP] El cliente Petopia ya existe. Saltando seed.")
    db.close()
    sys.exit(0)

# Crear cliente Petopia
client = Client(
    name="Petopia",
    description="Servicios veterinarios - Telefonía Yeastar + Botmaker",
    color="#3b7cff",
    logo_text="PT",
    kpi_modules=["petopia_vol", "calls"]
)
db.add(client)
db.flush()

# Datos de Mayo a Agosto 2026 para Petopia
# Totales Yeastar: May=53, Jun=251, Jul=12, Ago=12
# Botmaker estimado: 153 por mes
petopia_months = [
    (5, 53, 153),
    (6, 251, 153),
    (7, 12, 153),
    (8, 12, 153),
]

for m, yeastar, botmaker in petopia_months:
    report = MonthlyReport(
        client_id=client.id,
        year=2026,
        month=m,
        total_calls=yeastar,
        answered_calls=int(yeastar * 0.85),
        contact_rate=85.0,
        extra_data={
            "yeastar_calls": yeastar,
            "botmaker_interactions": botmaker,
            "total_interactions": yeastar + botmaker
        },
        notes=f"Reporte combinado Yeastar ({yeastar}) + Botmaker ({botmaker})"
    )
    db.add(report)

db.commit()
print(f"[OK] Cliente 'Petopia' creado con ID={client.id} y 4 meses de datos.")
db.close()
