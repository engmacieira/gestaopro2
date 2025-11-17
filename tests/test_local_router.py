import pytest
from fastapi.testclient import TestClient

def test_create_local(test_client: TestClient, admin_auth_headers: dict):
    """Testa POST /api/locais/"""
    response = test_client.post(
        "/api/locais/", 
        json={"descricao": "Local de Teste 1"}, 
        headers=admin_auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["descricao"] == "Local de Teste 1"
    assert data["id"] is not None

def test_get_local_by_id(test_client: TestClient, admin_auth_headers: dict):
    """Testa GET /api/locais/{id}"""
    response_create = test_client.post(
        "/api/locais/",
        json={"descricao": "Local de Teste 2"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/locais/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["descricao"] == "Local de Teste 2"
    assert data["id"] == new_id

def test_get_all_locais(test_client: TestClient, admin_auth_headers: dict):
    """Testa GET /api/locais/"""
    test_client.post("/api/locais/", json={"descricao": "Local A"}, headers=admin_auth_headers)
    test_client.post("/api/locais/", json={"descricao": "Local B"}, headers=admin_auth_headers)

    response_get = test_client.get("/api/locais/", headers=admin_auth_headers)
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "Local A" in [item["descricao"] for item in data]

def test_update_local(test_client: TestClient, admin_auth_headers: dict):
    """Testa PUT /api/locais/{id}"""
    response_create = test_client.post(
        "/api/locais/",
        json={"descricao": "Local Original"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_put = test_client.put(
        f"/api/locais/{new_id}",
        json={"descricao": "Local Atualizado"},
        headers=admin_auth_headers
    )
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["descricao"] == "Local Atualizado"

def test_delete_local(test_client: TestClient, admin_auth_headers: dict):
    """Testa DELETE /api/locais/{id}"""
    response_create = test_client.post(
        "/api/locais/",
        json={"descricao": "Local Para Deletar"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/locais/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/locais/{new_id}",
        headers=admin_auth_headers
    )

    assert response_get.status_code == 404