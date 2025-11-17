import pytest
from fastapi.testclient import TestClient

def test_create_tipo_documento(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.post(
        "/api/tipos-documento/", 
        json={"nome": "Nota Fiscal"}, 
        headers=admin_auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Nota Fiscal"
    assert data["id"] is not None

def test_get_tipo_documento_by_id(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/tipos-documento/",
        json={"nome": "Orçamento"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/tipos-documento/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["nome"] == "Orçamento"
    assert data["id"] == new_id

def test_get_all_tipos_documento(test_client: TestClient, admin_auth_headers: dict):
    test_client.post("/api/tipos-documento/", json={"nome": "Tipo Doc A"}, headers=admin_auth_headers)
    test_client.post("/api/tipos-documento/", json={"nome": "Tipo Doc B"}, headers=admin_auth_headers)

    response_get = test_client.get("/api/tipos-documento/", headers=admin_auth_headers)
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "Tipo Doc A" in [item["nome"] for item in data]

def test_update_tipo_documento(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/tipos-documento/",
        json={"nome": "Tipo Original"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_put = test_client.put(
        f"/api/tipos-documento/{new_id}",
        json={"nome": "Tipo Atualizado"},
        headers=admin_auth_headers
    )
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["nome"] == "Tipo Atualizado"

def test_delete_tipo_documento(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/tipos-documento/",
        json={"nome": "Tipo Para Deletar"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/tipos-documento/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/tipos-documento/{new_id}",
        headers=admin_auth_headers
    )

    assert response_get.status_code == 404