from app.database import engine, SessionLocal
from app.models import Base, Source, Client, KPIConfig

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Seed default sources if not present
default_sources = [
    ("Yeastar Call Center", "yeastar", "Sistema de telefonía IP y Call Center"),
    ("Botmaker Chatbot", "botmaker", "Plataforma de automatización de chats y bots"),
    ("Ingreso Manual", "manual", "Ingreso directo por formulario administrativo"),
]

for name, code, desc in default_sources:
    existing = db.query(Source).filter(Source.code == code).first()
    if not existing:
        db.add(Source(name=name, code=code, description=desc))
        print(f"[OK] Creada fuente: {name}")

db.commit()

# Seed default KPI configs for existing clients if empty
clients = db.query(Client).all()
for c in clients:
    if not c.kpi_configs:
        mods = c.kpi_modules or ["chat_sales", "appointments", "calls", "quality_kidoz"]
        for mod in mods:
            db.add(KPIConfig(
                client_id=c.id,
                kpi_code=mod,
                kpi_name=mod.replace("_", " ").title(),
                source_code="yeastar" if mod == "petopia_vol" else "manual"
            ))
        print(f"[OK] KPIConfigs generados para cliente: {c.name}")

db.commit()
db.close()
print("Migración Fase 01 completada exitosamente.")
