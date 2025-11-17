import pytest
from fastapi.testclient import TestClient

def test_create_instrumento(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.post(
        "/api/instrumentos/", 
        json={"nome": "Contrato de Teste 1"}, 
        headers=admin_auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Contrato de Teste 1"
    assert data["id"] is not None

def test_get_instrumento_by_id(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/instrumentos/",
        json={"nome": "Contrato de Teste 2"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/instrumentos/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["nome"] == "Contrato de Teste 2"
    assert data["id"] == new_id

def test_get_all_instrumentos(test_client: TestClient, admin_auth_headers: dict):
    test_client.post("/api/instrumentos/", json={"nome": "Contrato A"}, headers=admin_auth_headers)
    test_client.post("/api/instrumentos/", json={"nome": "Contrato B"}, headers=admin_auth_headers)

    response_get = test_client.get("/api/instrumentos/", headers=admin_auth_headers)
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "Contrato A" in [item["nome"] for item in data]

def test_update_instrumento(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/instrumentos/",
        json={"nome": "Contrato Original"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_put = test_client.put(
        f"/api/instrumentos/{new_id}",
        json={"nome": "Contrato Atualizado"},
        headers=admin_auth_headers
    )
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["nome"] == "Contrato Atualizado"

def test_delete_instrumento(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/instrumentos/",
        json={"nome": "Contrato Para Deletar"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/instrumentos/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/instrumentos/{new_id}",
        headers=admin_auth_headers
    )
    
    assert response_get.status_code == 404