import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from main import app

client = TestClient(app)


def test_metrics_endpoint():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data
    assert "network" in data
    assert "system" in data
    assert 0 <= data["cpu"]["percent"] <= 100
    assert 0 <= data["memory"]["percent"] <= 100
    assert 0 <= data["disk"]["percent"] <= 100


def test_history_endpoint():
    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data
    assert "timestamps" in data
    assert isinstance(data["cpu"], list)


def test_alerts_endpoint():
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert "thresholds" in data
    assert "cpu" in data["thresholds"]
    assert "memory" in data["thresholds"]
    assert "disk" in data["thresholds"]


def test_processes_endpoint():
    response = client.get("/api/processes")
    assert response.status_code == 200
    data = response.json()
    assert "processes" in data
    assert isinstance(data["processes"], list)
    if data["processes"]:
        p = data["processes"][0]
        assert "pid" in p
        assert "name" in p
        assert "cpu" in p
        assert "memory" in p


def test_update_thresholds():
    response = client.post("/api/thresholds?cpu=75&memory=80&disk=85")
    assert response.status_code == 200
    data = response.json()
    assert data["thresholds"]["cpu"] == 75
    assert data["thresholds"]["memory"] == 80
    assert data["thresholds"]["disk"] == 85


def test_metrics_data_types():
    response = client.get("/api/metrics")
    data = response.json()
    assert isinstance(data["cpu"]["percent"], float)
    assert isinstance(data["cpu"]["count"], int)
    assert isinstance(data["memory"]["used_gb"], float)
    assert isinstance(data["disk"]["total_gb"], float)
    assert isinstance(data["system"]["hostname"], str)
