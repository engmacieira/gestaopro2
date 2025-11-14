import pytest
from fastapi.testclient import TestClient
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreateRequest

# O 'admin_auth_headers' é pego automaticamente do conftest.py

# --- Fixture de Preparação ---
@pytest.fixture(scope="function")
def setup_test_user(db_session):
    """
    Cria um utilizador de teste padrão (nível 3) no banco.
    Isto é diferente do 'admin_auth_headers' (que cria um admin).
    """
    repo = UserRepository(db_session)
    user_data = UserCreateRequest(
        username="test_user_normal",
        password="password123", # A senha
        nivel_acesso=3,
        ativo=True
    )
    try:
        user = repo.create(user_data)
        db_session.commit() # Precisamos de commitar para o login encontrar
        return user
    except Exception as e:
        db_session.rollback()
        return repo.get_by_username("test_user_normal")

# --- Testes de Autenticação ---

def test_login_success(test_client: TestClient, setup_test_user):
    """Testa se um login bem-sucedido retorna um token."""
    
    # Nota: Usamos 'data' (Form Data) em vez de 'json'
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
    """Testa se uma senha errada é rejeitada."""
    response = test_client.post(
        "/api/auth/login",
        data={
            "username": "test_user_normal",
            "password": "senhaerrada" # Senha incorreta
        }
    )
    assert response.status_code == 401 # Unauthorized
    assert "Usuário ou senha incorretos" in response.json()["detail"]

def test_login_fail_wrong_user(test_client: TestClient):
    """Testa se um utilizador inexistente é rejeitado."""
    response = test_client.post(
        "/api/auth/login",
        data={
            "username": "utilizador_que_nao_existe",
            "password": "password123"
        }
    )
    assert response.status_code == 401 # Unauthorized
    assert "Usuário ou senha incorretos" in response.json()["detail"]

def test_read_users_me(test_client: TestClient, admin_auth_headers: dict):
    """
    Testa o endpoint 'users/me' para garantir que ele retorna
    as informações do utilizador com base no token.
    """
    response = test_client.get(
        "/api/auth/users/me", # <--- CORREÇÃO: Adiciona o prefixo /auth/
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "test_admin_user" # Confirma que é o admin
    assert data["nivel_acesso"] == 1