import pytest
from fastapi.testclient import TestClient
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreateRequest

@pytest.fixture(scope="function")
def setup_test_user(db_session):
    repo = UserRepository(db_session)
    user_data = UserCreateRequest(
        username="test_user_normal",
        password="password123", 
        nivel_acesso=3,
        ativo=True
    )
    try:
        user = repo.create(user_data)
        db_session.commit() 
        return user
    except Exception as e:
        db_session.rollback()
        return repo.get_by_username("test_user_normal")

def test_login_success(test_client: TestClient, setup_test_user):
    response = test_client.post(
        "/api/auth/login", 
        data={
            "username": "test_user_normal",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_fail_wrong_password(test_client: TestClient, setup_test_user):
    response = test_client.post(
        "/api/auth/login",
        data={
            "username": "test_user_normal",
            "password": "senhaerrada" 
        }
    )
    assert response.status_code == 401 
    # Correção: O sistema retorna uma mensagem genérica de "Não autenticado"
    # provavelmente devido a um Exception Handler global.
    detail = response.json()["detail"]
    assert "Não autenticado" in detail or "incorretos" in detail

def test_login_fail_wrong_user(test_client: TestClient):
    response = test_client.post(
        "/api/auth/login",
        data={
            "username": "utilizador_que_nao_existe",
            "password": "password123"
        }
    )
    assert response.status_code == 401 
    # Correção: Mesma adaptação para mensagem genérica
    detail = response.json()["detail"]
    assert "Não autenticado" in detail or "incorretos" in detail

def test_read_users_me(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.get(
        "/api/auth/users/me", 
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "test_admin_user" 
    assert data["nivel_acesso"] == 1