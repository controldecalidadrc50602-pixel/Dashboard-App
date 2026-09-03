import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.auth import create_access_token
from app.dependencies import seed_default_users

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_default_users(db)
    db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def get_headers(username: str, role: str):
    token = create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_01_login_roles():
    # Login superadmin
    res_admin = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res_admin.status_code == 200
    data_admin = res_admin.json()
    assert data_admin["role"] == "superadmin"

    # Login operador
    res_op = client.post("/api/auth/login", json={"username": "operador", "password": "rc506operador"})
    assert res_op.status_code == 200
    data_op = res_op.json()
    assert data_op["role"] == "operator"


def test_02_operator_restrictions_forbidden():
    op_headers = get_headers("operador", "operator")

    # Intentar crear cliente como operador -> 403 Forbidden
    res_create = client.post("/api/clients/", json={"name": "Cliente Prohibido"}, headers=op_headers)
    assert res_create.status_code == 403
    assert res_create.json()["detail"] == "Acceso denegado. Se requiere rol Super Admin"

    # Intentar editar cliente como operador -> 403 Forbidden
    res_update = client.put("/api/clients/1", json={"name": "Edit Prohibido"}, headers=op_headers)
    assert res_update.status_code == 403

    # Intentar eliminar cliente como operador -> 403 Forbidden
    res_delete = client.delete("/api/clients/1", headers=op_headers)
    assert res_delete.status_code == 403

    # Intentar crear usuario como operador -> 403 Forbidden
    res_user = client.post("/api/admin/users/", json={"username": "test_user", "password": "123"}, headers=op_headers)
    assert res_user.status_code == 403


def test_03_operator_allowed_reads_and_imports():
    op_headers = get_headers("operador", "operator")

    # Operador puede ver clientes
    res_clients = client.get("/api/clients/", headers=op_headers)
    assert res_clients.status_code == 200

    # Operador puede ver dashboard global
    res_dash = client.get("/api/admin/dashboard-global", headers=op_headers)
    assert res_dash.status_code == 200

    # Operador puede ver historial de ingestas
    res_imp = client.get("/api/admin/imports/", headers=op_headers)
    assert res_imp.status_code == 200


def test_04_superadmin_user_management():
    admin_headers = get_headers("admin", "superadmin")

    # Listar usuarios
    res_list = client.get("/api/admin/users/", headers=admin_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 2

    # Crear nuevo usuario
    res_create = client.post("/api/admin/users/", json={
        "username": "analista1",
        "password": "password123",
        "role": "operator",
        "full_name": "Analista de Datos",
        "email": "analista@rc506.com"
    }, headers=admin_headers)
    assert res_create.status_code == 201
    user_id = res_create.json()["id"]

    # Editar usuario (promover a superadmin)
    res_edit = client.put(f"/api/admin/users/{user_id}", json={
        "role": "superadmin",
        "full_name": "Analista Master"
    }, headers=admin_headers)
    assert res_edit.status_code == 200
    assert res_edit.json()["role"] == "superadmin"
    assert res_edit.json()["full_name"] == "Analista Master"

    # Desactivar usuario
    res_deactivate = client.put(f"/api/admin/users/{user_id}", json={
        "is_active": False
    }, headers=admin_headers)
    assert res_deactivate.status_code == 200
    assert res_deactivate.json()["is_active"] is False


def test_05_protect_last_superadmin():
    admin_headers = get_headers("admin", "superadmin")

    # Obtener lista de usuarios para hallar ID de admin
    res_list = client.get("/api/admin/users/", headers=admin_headers)
    users = res_list.json()
    admin_user = next(u for u in users if u["username"] == "admin")

    # Intentar desactivar al único superadmin -> 400 Bad Request
    res_deactivate = client.put(f"/api/admin/users/{admin_user['id']}", json={
        "is_active": False
    }, headers=admin_headers)
    assert res_deactivate.status_code == 400
    assert "último Super Admin" in res_deactivate.json()["detail"]

    # Intentar eliminar al único superadmin -> 400 Bad Request
    res_delete = client.delete(f"/api/admin/users/{admin_user['id']}", headers=admin_headers)
    assert res_delete.status_code == 400
    assert "último Super Admin" in res_delete.json()["detail"]
