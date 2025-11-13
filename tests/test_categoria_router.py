import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token 
from app.models.user_model import User 

@pytest.fixture
def admin_auth_headers(db_session): 
    
    from app.repositories.user_repository import UserRepository
    from app.schemas.user_schema import UserCreateRequest

    repo = UserRepository(db_session)
    user_data = UserCreateRequest(
        username="test_admin_user",
        password="password123",
        nivel_acesso=1, 
        ativo=True
    )
    try:
        admin_user = repo.create(user_data)
    except Exception as e:
        db_session.rollback()
        admin_user = repo.get_by_username("test_admin_user")
    
    token = create_access_token(admin_user)
    
    return {"Authorization": f"Bearer {token}"}


def test_create_categoria(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.post(
        "/api/categorias/",
        json={"nome": "Categoria de Teste 1"},
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201 
    data = response.json()
    assert data["nome"] == "Categoria de Teste 1"
    assert data["id"] is not None
    assert data["ativo"] is True

def test_get_categoria_by_id(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/categorias/",
        json={"nome": "Categoria de Teste 2"},
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    response_get = test_client.get(
        f"/api/categorias/{new_id}",
        headers=admin_auth_headers
    )
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["nome"] == "Categoria de Teste 2"
    assert data["id"] == new_id

def test_update_categoria(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/categorias/",
        json={"nome": "Categoria Original"},
        headers=admin_auth_headers
    )
    new_id = response_create.json()["id"]

    response_put = test_client.put(
        f"/api/categorias/{new_id}",
        json={"nome": "Categoria Atualizada"},
        headers=admin_auth_headers
    )
    
    assert response_put.status_code == 200
    data = response_put.json()
    assert data["nome"] == "Categoria Atualizada"
    assert data["id"] == new_id

def test_delete_categoria(test_client: TestClient, admin_auth_headers: dict):
    response_create = test_client.post(
        "/api/categorias/",
        json={"nome": "Categoria Para Deletar"},
        headers=admin_auth_headers
    )
    new_id = response_create.json()["id"]

    response_delete = test_client.delete(
        f"/api/categorias/{new_id}",
        headers=admin_auth_headers
    )
    
    assert response_delete.status_code == 204 

    response_get = test_client.get(
        f"/api/categorias/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 404 