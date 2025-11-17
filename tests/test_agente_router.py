import pytest
from fastapi.testclient import TestClient

def test_create_agente(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.post(
        "/api/agentes/", 
        json={"nome": "Agente de Teste 1"}, 
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Agente de Teste 1"
    assert data["id"] is not None

def test_get_agente_by_id(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/agentes/",
        json={"nome": "Agente de Teste 2"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/agentes/{new_id}",
        headers=admin_auth_headers
    )
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["nome"] == "Agente de Teste 2"
    assert data["id"] == new_id

def test_get_all_agentes(test_client: TestClient, admin_auth_headers: dict):
    response1 = test_client.post("/api/agentes/", json={"nome": "Agente A"}, headers=admin_auth_headers)
    response2 = test_client.post("/api/agentes/", json={"nome": "Agente B"}, headers=admin_auth_headers)
    assert response1.status_code == 201
    assert response2.status_code == 201

    response_get = test_client.get("/api/agentes/", headers=admin_auth_headers)
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list) 
    assert len(data) >= 2 
    assert "Agente A" in [item["nome"] for item in data]
    assert "Agente B" in [item["nome"] for item in data]

def test_update_agente(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/agentes/",
        json={"nome": "Agente Original"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_put = test_client.put(
        f"/api/agentes/{new_id}",
        json={"nome": "Agente Atualizado"}, 
        headers=admin_auth_headers
    )
    
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["nome"] == "Agente Atualizado"
    assert data["id"] == new_id

def test_delete_agente(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/agentes/",
        json={"nome": "Agente Para Deletar"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/agentes/{new_id}",
        headers=admin_auth_headers
    )
    
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/agentes/{new_id}",
        headers=admin_auth_headers
    )
    
    assert response_get.status_code == 404