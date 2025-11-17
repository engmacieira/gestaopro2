import pytest
from fastapi.testclient import TestClient

def test_create_modalidade(test_client: TestClient, admin_auth_headers: dict):
    """Testa POST /api/modalidades/"""
    response = test_client.post(
        "/api/modalidades/", 
        json={"nome": "Modalidade de Teste 1"}, 
        headers=admin_auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Modalidade de Teste 1"
    assert data["id"] is not None

def test_get_modalidade_by_id(test_client: TestClient, admin_auth_headers: dict):
    """Testa GET /api/modalidades/{id}"""
    response_create = test_client.post(
        "/api/modalidades/",
        json={"nome": "Modalidade de Teste 2"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/modalidades/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["nome"] == "Modalidade de Teste 2"
    assert data["id"] == new_id

def test_get_all_modalidades(test_client: TestClient, admin_auth_headers: dict):
    """Testa GET /api/modalidades/"""
    test_client.post("/api/modalidades/", json={"nome": "Modalidade A"}, headers=admin_auth_headers)
    test_client.post("/api/modalidades/", json={"nome": "Modalidade B"}, headers=admin_auth_headers)

    response_get = test_client.get("/api/modalidades/", headers=admin_auth_headers)
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "Modalidade A" in [item["nome"] for item in data]

def test_update_modalidade(test_client: TestClient, admin_auth_headers: dict):
    """Testa PUT /api/modalidades/{id}"""
    response_create = test_client.post(
        "/api/modalidades/",
        json={"nome": "Modalidade Original"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_put = test_client.put(
        f"/api/modalidades/{new_id}",
        json={"nome": "Modalidade Atualizada"},
        headers=admin_auth_headers
    )
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["nome"] == "Modalidade Atualizada"

def test_delete_modalidade(test_client: TestClient, admin_auth_headers: dict):
    """Testa DELETE /api/modalidades/{id}"""
    response_create = test_client.post(
        "/api/modalidades/",
        json={"nome": "Modalidade Para Deletar"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/modalidades/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/modalidades/{new_id}",
        headers=admin_auth_headers
    )

    assert response_get.status_code == 404