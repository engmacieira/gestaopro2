import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app
from app.models.user_model import User
from app.core.security import get_password_hash

# --- Fixtures ---

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_user():
    """Cria um usuário simulado para o teste"""
    return User(
        id=1,
        username="admin",
        password_hash=get_password_hash("senha123"), # Hash real para teste
        nivel_acesso=1,
        ativo=True
    )

@pytest.fixture
def override_dependencies(mock_user):
    """
    Sobrescreve a dependência de autenticação para simular um usuário logado.
    """
    from app.core.security import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides = {}

# --- Testes ---

def test_change_password_sucesso(client, override_dependencies, mock_user):
    """
    Testa o cenário feliz: Senha atual correta -> Nova senha salva.
    """
    # Payload com a senha atual correta e a nova senha
    payload = {
        "current_password": "senha123",
        "new_password": "nova_senha_456"
    }

    # Mockamos o Repositório dentro do Router
    with patch("app.routers.auth_router.UserRepository") as MockRepo:
        repo_instance = MockRepo.return_value
        
        # 1. get_by_id deve retornar o usuário atual (para pegar o hash antigo)
        repo_instance.get_by_id.return_value = mock_user
        
        # 2. update_password deve retornar True (sucesso)
        repo_instance.update_password.return_value = True

        # Executa a requisição
        response = client.post("/api/auth/change-password", json=payload)

        # Verificações
        assert response.status_code == 200
        assert response.json()["message"] == "Senha alterada com sucesso!"
        
        # Verifica se o update foi chamado corretamente
        repo_instance.update_password.assert_called_once()
        
        # Verifica se a senha salva foi um HASH, não texto plano
        args = repo_instance.update_password.call_args[0]
        nova_senha_salva = args[1] # Segundo argumento do método (new_password_hash)
        assert nova_senha_salva != "nova_senha_456" # Não pode ser igual ao texto puro
        assert "pbkdf2" in nova_senha_salva or "scrypt" in nova_senha_salva # Deve parecer um hash

def test_change_password_senha_atual_incorreta(client, override_dependencies, mock_user):
    """
    Testa se o sistema bloqueia a alteração quando a senha atual não confere.
    """
    payload = {
        "current_password": "senha_errada", # <--- ERRO AQUI
        "new_password": "nova_senha_456"
    }

    with patch("app.routers.auth_router.UserRepository") as MockRepo:
        repo_instance = MockRepo.return_value
        repo_instance.get_by_id.return_value = mock_user

        response = client.post("/api/auth/change-password", json=payload)

        # Deve retornar 400 Bad Request
        assert response.status_code == 400
        assert response.json()["detail"] == "A senha atual está incorreta."
        
        # O método de update no banco NUNCA deve ser chamado
        repo_instance.update_password.assert_not_called()

def test_change_password_usuario_nao_encontrado(client, override_dependencies):
    """
    Testa o caso raro onde o usuário está logado (token válido), 
    mas foi deletado do banco antes de trocar a senha.
    """
    payload = {
        "current_password": "senha123",
        "new_password": "nova_senha"
    }

    with patch("app.routers.auth_router.UserRepository") as MockRepo:
        repo_instance = MockRepo.return_value
        # Simula que o usuário não existe mais no banco
        repo_instance.get_by_id.return_value = None

        response = client.post("/api/auth/change-password", json=payload)

        assert response.status_code == 404
        assert response.json()["detail"] == "Usuário não encontrado."

def test_change_password_erro_banco(client, override_dependencies, mock_user):
    """
    Testa se a API trata erros inesperados do banco de dados (Retorna 500).
    """
    payload = {
        "current_password": "senha123",
        "new_password": "nova_senha"
    }

    with patch("app.routers.auth_router.UserRepository") as MockRepo:
        repo_instance = MockRepo.return_value
        repo_instance.get_by_id.return_value = mock_user
        
        # Simula falha no update (retorna False)
        repo_instance.update_password.return_value = False

        response = client.post("/api/auth/change-password", json=payload)

        assert response.status_code == 500
        assert "Erro ao atualizar" in response.json()["detail"]