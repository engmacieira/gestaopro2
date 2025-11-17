import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def user_payload() -> dict:
    return {
        "username": "trainee_user_teste",
        "password": "PasswordSegura123",
        "nivel_acesso": 3, 
        "ativo": True
    }

def test_create_user(test_client: TestClient, admin_auth_headers: dict, user_payload: dict):
    response = test_client.post(
        "/api/users/", 
        json=user_payload,
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "trainee_user_teste"
    assert data["nivel_acesso"] == 3
    assert data["id"] is not None

def test_get_user_by_id(test_client: TestClient, admin_auth_headers: dict, user_payload: dict):
    response_create = test_client.post(
        "/api/users/",
        json=user_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/users/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["id"] == new_id
    assert data["username"] == "trainee_user_teste"

def test_update_user(test_client: TestClient, admin_auth_headers: dict, user_payload: dict):
    response_create = test_client.post(
        "/api/users/",
        json=user_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    update_payload = {
        "username": "trainee_user_teste", 
        "nivel_acesso": 2 
    }
    response_put = test_client.put(
        f"/api/users/{new_id}",
        json=update_payload,
        headers=admin_auth_headers
    )
    
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["nivel_acesso"] == 2
    assert data["username"] == "trainee_user_teste"

def test_delete_user_soft_delete(test_client: TestClient, admin_auth_headers: dict, user_payload: dict):
    response_create = test_client.post(
        "/api/users/",
        json=user_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/users/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/users/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 404

def test_reset_user_password(test_client: TestClient, admin_auth_headers: dict, user_payload: dict):
    response_create = test_client.post(
        "/api/users/",
        json=user_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_reset = test_client.post(
        f"/api/users/{new_id}/reset-password",
        headers=admin_auth_headers
    )
    assert response_reset.status_code == 200
    data = response_reset.json()
    assert "new_password" in data
    assert len(data["new_password"]) == 12 