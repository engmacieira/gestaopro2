import pytest
from fastapi.testclient import TestClient

def test_create_dotacao(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.post(
        "/api/dotacoes/", 
        json={"info_orcamentaria": "01.01.01 - Teste"}, 
        headers=admin_auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["info_orcamentaria"] == "01.01.01 - Teste"
    assert data["id"] is not None

def test_get_dotacao_by_id(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/dotacoes/",
        json={"info_orcamentaria": "02.02.02 - Buscar"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/dotacoes/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["info_orcamentaria"] == "02.02.02 - Buscar"
    assert data["id"] == new_id

def test_get_all_dotacoes(test_client: TestClient, admin_auth_headers: dict):
    test_client.post("/api/dotacoes/", json={"info_orcamentaria": "Dotação A"}, headers=admin_auth_headers)
    test_client.post("/api/dotacoes/", json={"info_orcamentaria": "Dotação B"}, headers=admin_auth_headers)

    response_get = test_client.get("/api/dotacoes/", headers=admin_auth_headers)
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "Dotação A" in [item["info_orcamentaria"] for item in data]

def test_update_dotacao(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/dotacoes/",
        json={"info_orcamentaria": "Dotação Original"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_put = test_client.put(
        f"/api/dotacoes/{new_id}",
        json={"info_orcamentaria": "Dotação Atualizada"},
        headers=admin_auth_headers
    )
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["info_orcamentaria"] == "Dotação Atualizada"

def test_delete_dotacao(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/dotacoes/",
        json={"info_orcamentaria": "Dotação Para Deletar"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/dotacoes/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/dotacoes/{new_id}",
        headers=admin_auth_headers
    )

    assert response_get.status_code == 404