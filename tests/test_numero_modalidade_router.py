import pytest
from fastapi.testclient import TestClient

def test_create_numero_modalidade(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.post(
        "/api/numeros-modalidade/", 
        json={"numero_ano": "123/2025"}, 
        headers=admin_auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["numero_ano"] == "123/2025"
    assert data["id"] is not None

def test_get_numero_modalidade_by_id(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/numeros-modalidade/",
        json={"numero_ano": "456/2025"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/numeros-modalidade/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["numero_ano"] == "456/2025"
    assert data["id"] == new_id

def test_get_all_numeros_modalidade(test_client: TestClient, admin_auth_headers: dict):
    test_client.post("/api/numeros-modalidade/", json={"numero_ano": "789/2025"}, headers=admin_auth_headers)
    test_client.post("/api/numeros-modalidade/", json={"numero_ano": "101/2026"}, headers=admin_auth_headers)

    response_get = test_client.get("/api/numeros-modalidade/", headers=admin_auth_headers)
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "789/2025" in [item["numero_ano"] for item in data]

def test_update_numero_modalidade(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/numeros-modalidade/",
        json={"numero_ano": "Original/2025"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_put = test_client.put(
        f"/api/numeros-modalidade/{new_id}",
        json={"numero_ano": "Atualizado/2025"},
        headers=admin_auth_headers
    )
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["numero_ano"] == "Atualizado/2025"

def test_delete_numero_modalidade(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/numeros-modalidade/",
        json={"numero_ano": "ParaDeletar/2025"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/numeros-modalidade/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/numeros-modalidade/{new_id}",
        headers=admin_auth_headers
    )

    assert response_get.status_code == 404