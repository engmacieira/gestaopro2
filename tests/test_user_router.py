import pytest
from fastapi.testclient import TestClient

# O 'admin_auth_headers' é pego automaticamente do conftest.py

# --- Fixture de Dados (Payload) ---
@pytest.fixture
def user_payload() -> dict:
    """Retorna um payload JSON válido para criar um utilizador."""
    return {
        "username": "trainee_user_teste",
        "password": "PasswordSegura123",
        "nivel_acesso": 3, # Visualização
        "ativo": True
    }

# --- Testes do CRUD ---

def test_create_user(test_client: TestClient, admin_auth_headers: dict, user_payload: dict):
    """Testa POST /api/users/"""
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
    """Testa GET /api/users/{id}"""
    # 1. Criar
    response_create = test_client.post(
        "/api/users/",
        json=user_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Buscar por ID
    response_get = test_client.get(
        f"/api/users/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["id"] == new_id
    assert data["username"] == "trainee_user_teste"

def test_update_user(test_client: TestClient, admin_auth_headers: dict, user_payload: dict):
    """Testa PUT /api/users/{id} (não mexe na senha)"""
    # 1. Criar
    response_create = test_client.post(
        "/api/users/",
        json=user_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Atualizar (mudar nível de acesso)
    update_payload = {
        "username": "trainee_user_teste", # O username é obrigatório no PUT (ou Pydantic falha)
        "nivel_acesso": 2 # Promovido para Usuário Completo
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
    """Testa DELETE /api/users/{id} (que é um soft delete)"""
    # 1. Criar
    response_create = test_client.post(
        "/api/users/",
        json=user_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Deletar (Soft Delete)
    response_delete = test_client.delete(
        f"/api/users/{new_id}",
        headers=admin_auth_headers
    )
    assert response_delete.status_code == 204 

    # 3. Verificar (deve dar 404, pois get_by_id só busca ativos)
    response_get = test_client.get(
        f"/api/users/{new_id}",
        headers=admin_auth_headers
    )
    assert response_get.status_code == 404

def test_reset_user_password(test_client: TestClient, admin_auth_headers: dict, user_payload: dict):
    """Testa POST /api/users/{id}/reset-password"""
    # 1. Criar
    response_create = test_client.post(
        "/api/users/",
        json=user_payload,
        headers=admin_auth_headers
    )
    assert response_create.status_code == 201
    new_id = response_create.json()["id"]

    # 2. Resetar a senha
    response_reset = test_client.post(
        f"/api/users/{new_id}/reset-password",
        headers=admin_auth_headers
    )
    assert response_reset.status_code == 200
    data = response_reset.json()
    assert "new_password" in data
    assert len(data["new_password"]) == 12 # Verifica se gerou a senha de 12 chars