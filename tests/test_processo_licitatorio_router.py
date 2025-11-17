import pytest
from fastapi.testclient import TestClient

def test_create_processo(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.post(
        "/api/processos-licitatorios/", 
        json={"numero": "PL 001/2025"}, 
        headers=admin_auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["numero"] == "PL 001/2025"
    assert data["id"] is not None

def test_get_processo_by_id(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/processos-licitatorios/",
        json={"numero": "PL 002/2025"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/processos-licitatorios/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["numero"] == "PL 002/2025"
    assert data["id"] == new_id

def test_get_all_processos(test_client: TestClient, admin_auth_headers: dict):
    test_client.post("/api/processos-licitatorios/", json={"numero": "PL A"}, headers=admin_auth_headers)
    test_client.post("/api/processos-licitatorios/", json={"numero": "PL B"}, headers=admin_auth_headers)

    response_get = test_client.get("/api/processos-licitatorios/", headers=admin_auth_headers)
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "PL A" in [item["numero"] for item in data]

def test_update_processo(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/processos-licitatorios/",
        json={"numero": "PL Original"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_put = test_client.put(
        f"/api/processos-licitatorios/{new_id}",
        json={"numero": "PL Atualizado"},
        headers=admin_auth_headers
    )
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["numero"] == "PL Atualizado"

def test_delete_processo(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/processos-licitatorios/",
        json={"numero": "PL Para Deletar"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/processos-licitatorios/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/processos-licitatorios/{new_id}",
        headers=admin_auth_headers
    )

    assert response_get.status_code == 404