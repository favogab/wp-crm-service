import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import database


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    # Keep test records separate from the development database.
    test_db = tmp_path / "test_crm.db"
    monkeypatch.setattr(database, "DATABASE_PATH", test_db)
    database.initialize_database()

@pytest.fixture(autouse=True)
def test_api_key(monkeypatch):
    # Use a dedicated API key without changing development settings.
    monkeypatch.setattr("app.main.CRM_API_KEY", "test-secret-key")



def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_missing_api_key():
    # Send a valid lead without providing an API key.
    # The CRM must reject unauthenticated requests.
    response = client.post(
        "/api/leads",
        json={
            "reference": "TEST-000001",
            "name": "Test User",
            "email": "test@example.com",
            "message": "Testing authentication."
        }
    )

    assert response.status_code == 401


def test_invalid_api_key():
    # Supply an incorrect API key.
    # A random key must never grant access to the CRM.
    response = client.post(
        "/api/leads",
        headers={
            "X-API-Key": "invalid-test-key"
        },
        json={
            "reference": "TEST-000002",
            "name": "Test User",
            "email": "test@example.com",
            "message": "Testing invalid credentials."
        }
    )

    assert response.status_code == 401


def test_create_lead():
    # Verify that an authenticated lead is accepted and acknowledged.
    payload = {
        "reference": "WP-TEST-CRM-000001",
        "name": "Test Customer",
        "email": "customer@example.com",
        "message": "Testing CRM integration."
    }

    with TestClient(app) as client:
        response = client.post(
            "/api/leads",
            json=payload,
            headers = {"X-API-Key": "test-secret-key"}
        )

    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert data["reference"] == payload["reference"]


def test_duplicate_lead():
    # Repeating an identical lead must not create another record.
    payload = {
        "reference": "WP-TEST-CRM-000002",
        "name": "Duplicate Customer",
        "email": "duplicate@example.com",
        "message": "Testing duplicate prevention."
    }

    with TestClient(app) as client:
        headers = {"X-API-Key": "test-secret-key"}

        first = client.post("/api/leads", json=payload, headers=headers)
        second = client.post("/api/leads", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["reference"] == payload["reference"]

    assert database.find_lead(payload["reference"]) is not None


def test_conflicting_lead():
    # Reusing a reference with different data must be rejected.
    payload = {
        "reference": "WP-TEST-CRM-000003",
        "name": "Original Customer",
        "email": "original@example.com",
        "message": "Original message."
    }

    with TestClient(app) as client:
        headers = {"X-API-Key": "test-secret-key"}

        first = client.post("/api/leads", json=payload, headers=headers)

        changed_payload = {
            **payload,
            "email": "different@example.com"
        }

        second = client.post(
            "/api/leads",
            json=changed_payload,
            headers=headers
        )

    assert first.status_code == 201
    assert second.status_code == 409

    stored = database.find_lead(payload["reference"])
    assert stored["email"] == "original@example.com"
