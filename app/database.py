from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

if os.getenv("VERCEL"):
    default_db = "sqlite:////tmp/dashboard.db"
else:
    default_db = "sqlite:///./dashboard.db"

DATABASE_URL = os.getenv("DATABASE_URL", default_db)

# Normalizar URLs de Supabase/Heroku/Render de 'postgres://' a 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine_kwargs = {}
if "sqlite" in DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Optimización de pool relacional para Supabase / PostgreSQL Serverless
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

_tables_created = False


def ensure_db_tables():
    """Garantiza la creación idempotente de todas las tablas ORM en Supabase / PostgreSQL / SQLite."""
    global _tables_created
    if not _tables_created:
        try:
            import app.models  # Importar explícitamente todos los modelos SQLAlchemy
            Base.metadata.create_all(bind=engine)
            _tables_created = True
        except Exception as e:
            print(f"Advertencia al verificar o crear tablas de BD: {e}")


def get_db():
    ensure_db_tables()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
