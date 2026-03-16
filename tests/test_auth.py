"""
Integration tests for the Secure Enterprise Auth System.

These tests use FastAPI's TestClient (backed by httpx) so no live server is needed.
The SQLite in-memory engine is created once per session for isolation and speed.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.utils.database import Base, get_db

# ── In-memory SQLite for tests ─────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test_auth.db"

test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def client(setup_database):
    with TestClient(app) as c:
        yield c


# ── Health check ───────────────────────────────────────────────────────────────

def test_health_check(client):
    response = client.get("/auth/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ── Registration ───────────────────────────────────────────────────────────────

def test_register_success(client):
    response = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "SecurePass1"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "user_id" in data
    assert data["message"] == "Account created successfully."


def test_register_duplicate_email(client):
    payload = {"email": "bob@example.com", "password": "SecurePass1"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400


def test_register_weak_password_too_short(client):
    response = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "Ab1"},
    )
    assert response.status_code == 422


def test_register_weak_password_no_uppercase(client):
    response = client.post(
        "/auth/register",
        json={"email": "weak@example.com", "password": "alllowercase1"},
    )
    assert response.status_code == 422


def test_register_weak_password_no_digit(client):
    response = client.post(
        "/auth/register",
        json={"email": "nodigit@example.com", "password": "NoDigitHere"},
    )
    assert response.status_code == 422


def test_register_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "SecurePass1"},
    )
    assert response.status_code == 422


# ── Login ──────────────────────────────────────────────────────────────────────

def test_login_success(client):
    client.post(
        "/auth/register",
        json={"email": "carol@example.com", "password": "SecurePass1"},
    )
    response = client.post(
        "/auth/login",
        json={"email": "carol@example.com", "password": "SecurePass1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "csrf_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={"email": "dave@example.com", "password": "SecurePass1"},
    )
    response = client.post(
        "/auth/login",
        json={"email": "dave@example.com", "password": "WrongPass9"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "SecurePass1"},
    )
    assert response.status_code == 401


# ── Token refresh ──────────────────────────────────────────────────────────────

def test_refresh_token_success(client):
    client.post(
        "/auth/register",
        json={"email": "eve@example.com", "password": "SecurePass1"},
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": "eve@example.com", "password": "SecurePass1"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_token_invalid(client):
    response = client.post("/auth/refresh", json={"refresh_token": "totally.invalid.token"})
    assert response.status_code == 401
