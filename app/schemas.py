from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ──────────────────────────────────────────────
# Client
# ──────────────────────────────────────────────
class ClientCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#009688"
    logo_text: str = "RC"
    kpi_modules: List[str] = ["chat_sales", "appointments", "calls", "quality_kidoz"]

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    logo_text: Optional[str] = None
    is_active: Optional[bool] = None
    kpi_modules: Optional[List[str]] = None

class ClientOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str
    logo_text: str
    is_active: bool
    kpi_modules: Optional[List[str]] = ["chat_sales", "appointments", "calls", "quality_kidoz"]
    created_at: datetime
    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Monthly Report
# ──────────────────────────────────────────────
class ReportCreate(BaseModel):
    year: int
    month: int = Field(..., ge=1, le=12)
    chats: int = 0
    leads: int = 0
    sales: int = 0
    appointment_confirmations: int = 0
    support: int = 0
    csat: float = 0.0
    total_calls: int = 0
    answered_calls: int = 0
    contact_rate: float = 0.0
    inbound_calls: int = 0
    inbound_answered: int = 0
    outbound_calls: int = 0
    outbound_answered: int = 0
    kidoz_optimal_calls: int = 0
    kidoz_optimal_chats: int = 0
    kidoz_acceptable_calls: int = 0
    kidoz_acceptable_chats: int = 0
    kidoz_deficient_calls: int = 0
    kidoz_deficient_chats: int = 0
    kidoz_total_evaluations: int = 0
    kidoz_optimal_pct: float = 0.0
    cancellation_data: Optional[Dict[str, Any]] = None
    support_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class ReportUpdate(ReportCreate):
    year: Optional[int] = None
    month: Optional[int] = None

class ReportOut(ReportCreate):
    id: int
    client_id: int
    created_at: datetime
    updated_at: datetime
    # Campos calculados
    closing_rate: Optional[float] = None
    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Public View
# ──────────────────────────────────────────────
SECTION_CHOICES = [
    "general", "datosmes", "chats", "llamadas",
    "equipo", "calidad", "soporte", "noagenda"
]

class PublicViewCreate(BaseModel):
    title: str
    description: Optional[str] = None
    visible_sections: List[str] = SECTION_CHOICES
    show_year: Optional[int] = None
    show_months_from: Optional[int] = None
    show_months_to: Optional[int] = None
    password: Optional[str] = None
    expires_at: Optional[datetime] = None

class PublicViewOut(BaseModel):
    id: int
    client_id: int
    token: str
    title: str
    description: Optional[str]
    visible_sections: List[str]
    show_year: Optional[int]
    show_months_from: Optional[int]
    show_months_to: Optional[int]
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    views_count: int
    has_password: bool = False
    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Sources & KPI Configs
# ──────────────────────────────────────────────
class SourceOut(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class KPIConfigOut(BaseModel):
    id: int
    client_id: int
    kpi_code: str
    kpi_name: str
    description: Optional[str] = None
    source_code: Optional[str] = None
    report_type: Optional[str] = None
    target_value: Optional[float] = None
    formula_type: str = "ratio"
    formula_expression: str = "a / b * 100"
    input_metrics: List[str] = []
    direction: str = "higher_is_better"
    unit: str = "percentage"
    period_frequency: str = "monthly"
    thresholds: Dict[str, Any] = {}
    is_active: bool
    version: str = "v1.0"
    created_at: datetime
    class Config:
        from_attributes = True



# ──────────────────────────────────────────────
# Audit Log
# ──────────────────────────────────────────────
class AuditLogOut(BaseModel):
    id: int
    username: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    timestamp: datetime
    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Dashboard Global RC506 Schemas
# ──────────────────────────────────────────────
class PreliminaryAlertOut(BaseModel):
    id: str
    type: str  # warning, danger, info, success
    title: str
    message: str
    client_id: Optional[int] = None
    client_name: Optional[str] = None

class ClientStatusOut(BaseModel):
    id: int
    name: str
    color: str
    logo_text: str
    is_active: bool
    period: str
    status: str  # actualizado, pendiente, requiere_configuracion, inactivo
    status_label: str
    kpis_count: int
    has_data: bool
    total_reports: int
    latest_report_year: Optional[int] = None
    latest_report_month: Optional[int] = None
    latest_report_month_name: Optional[str] = None

class GlobalSummaryOut(BaseModel):
    total_active_clients: int
    clients_with_data: int
    updated_reports_count: int
    pending_reports_count: int
    latest_period: Dict[str, Any]

class GlobalMetricsOut(BaseModel):
    total_chats: int
    total_calls: int
    total_leads: int
    total_sales: int
    avg_csat: float

class DashboardGlobalResponse(BaseModel):
    summary: GlobalSummaryOut
    client_statuses: List[ClientStatusOut]
    global_metrics: GlobalMetricsOut
    preliminary_alerts: List[PreliminaryAlertOut]
    recent_activity: List[AuditLogOut]


# ──────────────────────────────────────────────
# Ingesta y Conservación de Fuentes Schemas (Fase 02)
# ──────────────────────────────────────────────
class RowValidationErrorOut(BaseModel):
    row: int
    field: str
    message: str
    severity: str  # WARNING, ERROR

class ReportImportOut(BaseModel):
    id: int
    client_id: int
    client_name: Optional[str] = None
    source_code: str
    report_type: Optional[str]
    period: Optional[str]
    original_filename: str
    file_format: str
    file_size: int
    file_hash: str
    status: str  # RECEIVED, VALIDATING, VALID, VALID_WITH_WARNINGS, INVALID, DUPLICATE
    records_count: int
    warnings: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    metadata_info: Dict[str, Any] = {}
    uploaded_by: str
    created_at: datetime
    class Config:
        from_attributes = True

class ReportImportPreview(BaseModel):
    import_id: int
    original_filename: str
    source_code: str
    client_name: str
    report_type: Optional[str]
    period: str
    file_hash: str
    file_format: str
    file_size: int
    status: str
    delimiter: str
    encoding: str
    headers: List[str]
    sample_rows: List[List[str]]
    total_rows: int
    warnings: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []


# ──────────────────────────────────────────────
# Motor KPI Dinámico Schemas (Fase 04)
# ──────────────────────────────────────────────
class KPIConfigCreate(BaseModel):
    kpi_code: str
    kpi_name: str
    description: Optional[str] = None
    source_code: Optional[str] = None
    report_type: Optional[str] = None
    target_value: Optional[float] = None
    formula_type: str = "ratio"
    formula_expression: str = "a / b * 100"
    input_metrics: List[str] = []
    direction: str = "higher_is_better"
    unit: str = "percentage"
    period_frequency: str = "monthly"
    thresholds: Dict[str, Any] = {}
    is_active: bool = True
    version: str = "v1.0"

class KPIConfigUpdate(BaseModel):
    kpi_name: Optional[str] = None
    description: Optional[str] = None
    source_code: Optional[str] = None
    report_type: Optional[str] = None
    target_value: Optional[float] = None
    formula_type: Optional[str] = None
    formula_expression: Optional[str] = None
    input_metrics: Optional[List[str]] = None
    direction: Optional[str] = None
    unit: Optional[str] = None
    period_frequency: Optional[str] = None
    thresholds: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    version: Optional[str] = None

class KPIResultOut(BaseModel):
    id: int
    client_id: int
    kpi_config_id: int
    import_id: Optional[int] = None
    period: str
    kpi_code: str
    source_code: str
    value: Optional[float] = None
    target_value: Optional[float] = None
    status: str
    status_color: str
    formula_used: Optional[str] = None
    input_values: Dict[str, Any] = {}
    traceability_info: Dict[str, Any] = {}
    calculated_at: datetime
    class Config:
        from_attributes = True



