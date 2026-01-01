"""Testes para endpoints da API."""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app


@pytest.fixture
def client():
    """Cliente de teste."""
    return TestClient(app)


def test_health_endpoint(client):
    """Testa health check."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "version" in data
    assert "uptime_seconds" in data


def test_root_endpoint(client):
    """Testa root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data


def test_list_methods(client):
    """Testa listagem de métodos."""
    response = client.get("/methods")

    assert response.status_code == 200
    methods = response.json()
    assert len(methods) > 0
    assert any(m["name"] == "isolation-forest" for m in methods)


def test_detect_anomalies():
    """Testa detecção de anomalias."""
    # Prepara dados de teste
    start = datetime.now()
    data_points = []

    for i in range(50):
        data_points.append({
            "timestamp": (start + timedelta(minutes=i)).isoformat(),
            "value": 50.0 + (i % 10)
        })

    # Injeta anomalia
    data_points[25]["value"] = 200.0

    request_data = {
        "series": [
            {
                "resource_id": "test-pod-001",
                "metric_name": "cpu",
                "data": data_points
            }
        ],
        "method": "isolation-forest",
        "sensitivity": "medium"
    }

    response = client.post("/api/v1/detect", json=request_data)

    assert response.status_code == 200
    result = response.json()

    assert "results" in result
    assert len(result["results"]) == 1
    assert result["results"][0]["resource_id"] == "test-pod-001"
    assert result["results"][0]["anomaly_count"] > 0


@pytest.mark.asyncio
async def test_detect_multiple_series():
    """Testa detecção em múltiplas séries."""
    start = datetime.now()
    data_points = [
        {
            "timestamp": (start + timedelta(minutes=i)).isoformat(),
            "value": 50.0
        }
        for i in range(20)
    ]

    request_data = {
        "series": [
            {
                "resource_id": "pod-001",
                "metric_name": "cpu",
                "data": data_points
            },
            {
                "resource_id": "pod-002",
                "metric_name": "memory",
                "data": data_points
            }
        ],
        "method": "z-score",
        "sensitivity": "low"
    }

    response = client.post("/api/v1/detect", json=request_data)

    assert response.status_code == 200
    result = response.json()
    assert result["total_series"] == 2
