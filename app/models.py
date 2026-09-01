from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, default="#009688")
    logo_text = Column(String, default="RC")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Lista de módulos KPI activos para este cliente.
    kpi_modules = Column(JSON, default=lambda: ["chat_sales", "appointments", "calls", "quality_kidoz"])

    reports = relationship("MonthlyReport", back_populates="client", cascade="all, delete-orphan")
    public_views = relationship("PublicView", back_populates="client", cascade="all, delete-orphan")
    kpi_configs = relationship("KPIConfig", back_populates="client", cascade="all, delete-orphan")
    imports = relationship("ReportImport", back_populates="client", cascade="all, delete-orphan")
    normalized_records = relationship("NormalizedRecord", back_populates="client", cascade="all, delete-orphan")
    kpi_results = relationship("KPIResult", back_populates="client", cascade="all, delete-orphan")





class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Ej: Yeastar, Botmaker, Manual
    code = Column(String, unique=True, nullable=False, index=True)  # Ej: yeastar, botmaker, manual
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class KPIConfig(Base):
    __tablename__ = "kpi_configs"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    kpi_code = Column(String, nullable=False)  # Ej: chat_sales, petopia_vol, csat, sla_ citas
    kpi_name = Column(String, nullable=False)  # Ej: Conversión de Chats, SLA de Citas
    description = Column(Text, nullable=True)
    source_code = Column(String, nullable=True)  # Ej: yeastar, botmaker, manual
    report_type = Column(String, nullable=True)  # Ej: users, operatorsSessionsDebug, queue
    target_value = Column(Float, nullable=True)  # Meta/Objetivo (NULL = NO_TARGET)
    formula_type = Column(String, default="ratio")  # ratio, difference, percentage_gap, direct, linear_combination
    formula_expression = Column(String, default="a / b * 100")
    input_metrics = Column(JSON, default=list)  # ["answered", "total"]
    direction = Column(String, default="higher_is_better")  # higher_is_better, lower_is_better, range
    unit = Column(String, default="percentage")  # count, percentage, seconds, duration, NOT_VERIFIED
    period_frequency = Column(String, default="monthly")  # monthly, weekly, daily
    thresholds = Column(JSON, default=dict)  # {"warning": 80.0, "danger": 70.0}
    is_active = Column(Boolean, default=True)
    version = Column(String, default="v1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = relationship("Client", back_populates="kpi_configs")
    kpi_results = relationship("KPIResult", back_populates="kpi_config", cascade="all, delete-orphan")


class KPIResult(Base):
    __tablename__ = "kpi_results"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    kpi_config_id = Column(Integer, ForeignKey("kpi_configs.id"), nullable=False, index=True)
    import_id = Column(Integer, ForeignKey("report_imports.id"), nullable=True, index=True)
    period = Column(String, nullable=False, index=True)  # YYYY-MM
    kpi_code = Column(String, nullable=False)
    source_code = Column(String, nullable=False)
    value = Column(Float, nullable=True)  # Valor calculado (NULL si datos no disponibles)
    target_value = Column(Float, nullable=True)  # Objetivo al momento del cálculo
    status = Column(String, default="NO_DATA")  # NO_DATA, NOT_AVAILABLE, NO_TARGET, ON_TARGET, BELOW_TARGET, ABOVE_TARGET, INVALID
    status_color = Column(String, default="gray")  # green, yellow, orange, red, gray
    formula_used = Column(String, nullable=True)
    input_values = Column(JSON, default=dict)  # Valores de entrada utilizados
    traceability_info = Column(JSON, default=dict)  # Metadata de trazabilidad a import y normalizer
    calculated_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="kpi_results")
    kpi_config = relationship("KPIConfig", back_populates="kpi_results")



class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    action = Column(String, nullable=False)  # LOGIN, CREATE_CLIENT, UPDATE_REPORT, DELETE_VIEW, etc.
    resource_type = Column(String, nullable=False)  # client, report, public_view, dashboard
    resource_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class MonthlyReport(Base):
    __tablename__ = "monthly_reports"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12

    # KPIs principales
    chats = Column(Integer, default=0)
    leads = Column(Integer, default=0)
    sales = Column(Integer, default=0)
    appointment_confirmations = Column(Integer, default=0)
    support = Column(Integer, default=0)
    csat = Column(Float, default=0.0)

    # Llamadas
    total_calls = Column(Integer, default=0)
    answered_calls = Column(Integer, default=0)
    contact_rate = Column(Float, default=0.0)
    inbound_calls = Column(Integer, default=0)
    inbound_answered = Column(Integer, default=0)
    outbound_calls = Column(Integer, default=0)
    outbound_answered = Column(Integer, default=0)

    # Calidad KIDOZ
    kidoz_optimal_calls = Column(Integer, default=0)
    kidoz_optimal_chats = Column(Integer, default=0)
    kidoz_acceptable_calls = Column(Integer, default=0)
    kidoz_acceptable_chats = Column(Integer, default=0)
    kidoz_deficient_calls = Column(Integer, default=0)
    kidoz_deficient_chats = Column(Integer, default=0)
    kidoz_total_evaluations = Column(Integer, default=0)
    kidoz_optimal_pct = Column(Float, default=0.0)

    # Cancelaciones / No agendamiento (JSON por flexibilidad)
    cancellation_data = Column(JSON, nullable=True)

    # Soporte (JSON)
    support_data = Column(JSON, nullable=True)

    # Notas/insights del mes
    notes = Column(Text, nullable=True)

    # Datos adicionales / KPIs personalizados (Yeastar, Botmaker, heatmaps, etc.)
    extra_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = relationship("Client", back_populates="reports")


class PublicView(Base):
    __tablename__ = "public_views"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    # Secciones que el cliente puede ver
    visible_sections = Column(JSON, default=list)
    # Rango de meses a mostrar: None = todos
    show_year = Column(Integer, nullable=True)
    show_months_from = Column(Integer, nullable=True)
    show_months_to = Column(Integer, nullable=True)
    # Protección opcional con contraseña
    password_hash = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    views_count = Column(Integer, default=0)

    client = relationship("Client", back_populates="public_views")



class ReportImport(Base):
    __tablename__ = "report_imports"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    source_code = Column(String, nullable=False)  # botmaker, yeastar, manual
    report_type = Column(String, nullable=True)  # users, operatorsSessionsDebug, sessionStartingCauses, Extension, etc.
    period = Column(String, nullable=True)  # YYYY-MM o requiere_confirmacion
    original_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)  # uploads/raw/<uuid>.<ext>
    file_format = Column(String, nullable=False)  # tsv, csv, xlsx, txt
    file_size = Column(Integer, default=0)
    file_hash = Column(String, index=True, nullable=False)  # SHA-256
    status = Column(String, default="RECEIVED")  # RECEIVED, VALIDATING, VALID, VALID_WITH_WARNINGS, INVALID, DUPLICATE
    records_count = Column(Integer, default=0)
    warnings = Column(JSON, default=list)
    errors = Column(JSON, default=list)
    metadata_info = Column(JSON, default=dict)
    uploaded_by = Column(String, default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="imports")
    normalized_records = relationship("NormalizedRecord", back_populates="import_rel", cascade="all, delete-orphan")


class NormalizedRecord(Base):
    __tablename__ = "normalized_records"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    import_id = Column(Integer, ForeignKey("report_imports.id"), nullable=False, index=True)
    source_code = Column(String, nullable=False)  # botmaker, yeastar, manual
    report_type = Column(String, nullable=False)  # users, operatorsSessionsDebug, sessionStartingCauses, etc.
    period = Column(String, nullable=True)  # YYYY-MM
    row_number = Column(Integer, nullable=False)  # Trazabilidad directa a la fila de origen
    parser_version = Column(String, default="v1.0")  # Versión del parser utilizado
    event_id = Column(String, nullable=True)  # ID conversación o sesión
    user_id = Column(String, nullable=True)  # ID contacto/usuario/teléfono
    channel = Column(String, nullable=True)  # WhatsApp, Web, etc.
    agent = Column(String, nullable=True)  # Nombre/ID del agente u operador
    queue = Column(String, nullable=True)  # Cola de atención
    start_at = Column(DateTime, nullable=True)  # Timestamp de inicio
    end_at = Column(DateTime, nullable=True)  # Timestamp de fin
    wait_time_seconds = Column(Float, nullable=True)  # Tiempo de espera (NULL si no disponible)
    duration_seconds = Column(Float, nullable=True)  # Duración de atención (NULL si no disponible)
    messages_count = Column(Integer, nullable=True)  # Conteo de mensajes (NULL si no disponible)
    is_abandoned = Column(Boolean, nullable=True)  # Abandono (NULL si no disponible)
    typification = Column(String, nullable=True)  # Categorización/Tipificación
    quality_status = Column(String, default="VALID")  # VALID, VALID_WITH_WARNINGS, INVALID
    raw_data = Column(JSON, default=dict)  # Datos crudos recibidos
    normalized_data = Column(JSON, default=dict)  # Mapeo estándar normalizado
    warnings = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="normalized_records")
    import_rel = relationship("ReportImport", back_populates="normalized_records")


