import pytest
from fastapi.testclient import TestClient

# O 'admin_auth_headers' é pego automaticamente do conftest.py

def test_create_unidade(test_client: TestClient, admin_auth_headers: dict):
    """Testa POST /api/unidades/"""
    response = test_client.post(
        "/api/unidades/", 
        json={"nome": "Unidade de Teste 1"}, # Schema da Unidade
        headers=admin_auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Unidade de Teste 1"
    assert data["id"] is not None

def test_get_unidade_by_id(test_client: TestClient, admin_auth_headers: dict):
    """Testa GET /api/unidades/{id}"""
    response_create = test_client.post(
        "/api/unidades/",
        json={"nome": "Unidade de Teste 2"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/unidades/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["nome"] == "Unidade de Teste 2"
    assert data["id"] == new_id

def test_get_all_unidades(test_client: TestClient, admin_auth_headers: dict):
    """Testa GET /api/unidades/"""
    test_client.post("/api/unidades/", json={"nome": "Unidade A"}, headers=admin_auth_headers)
    test_client.post("/api/unidades/", json={"nome": "Unidade B"}, headers=admin_auth_headers)

    response_get = test_client.get("/api/unidades/", headers=admin_auth_headers)
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "Unidade A" in [item["nome"] for item in data]

def test_update_unidade(test_client: TestClient, admin_auth_headers: dict):
    """Testa PUT /api/unidades/{id}"""
    response_create = test_client.post(
        "/api/unidades/",
        json={"nome": "Unidade Original"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_put = test_client.put(
        f"/api/unidades/{new_id}",
        json={"nome": "Unidade Atualizada"},
        headers=admin_auth_headers
    )
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["nome"] == "Unidade Atualizada"

def test_delete_unidade(test_client: TestClient, admin_auth_headers: dict):
    """Testa DELETE /api/unidades/{id}"""
    response_create = test_client.post(
        "/api/unidades/",
        json={"nome": "Unidade Para Deletar"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/unidades/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/unidades/{new_id}",
        headers=admin_auth_headers
    )
    # Como você fez a Tarefa 1, este teste deve passar
    assert response_get.status_code == 404