import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch
from app.repositories.pedido_repository import PedidoRepository
from app.schemas.pedido_schema import RegistrarEntregaLoteRequest, EntregaItemLote
from app.models.pedido_model import Pedido

# --- Mocks e Dados de Teste ---

@pytest.fixture
def mock_db_conn():
    """Mock da conexão com o banco de dados"""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn

@pytest.fixture
def pedido_pendente():
    """Cria um objeto Pedido fictício para testes"""
    return Pedido(
        id=1,
        id_item_contrato=10,
        id_aocs=5,
        quantidade_pedida=Decimal('100.00'),
        data_pedido=date.today(),
        status_entrega='Pendente',
        quantidade_entregue=Decimal('0.00')
    )

# --- Testes Unitários do Repositório ---

def test_registrar_entrega_lote_sucesso(mock_db_conn, pedido_pendente):
    """
    Testa se o método atualiza corretamente o saldo e o status para 'Entregue'
    quando a quantidade fecha o total.
    """
    # 1. Configura o Mock
    repo = PedidoRepository(mock_db_conn)
    
    # Simula o get_by_id retornando nosso pedido pendente
    repo.get_by_id = MagicMock(return_value=pedido_pendente)
    
    # 2. Prepara os dados de entrada (Request)
    lote_req = RegistrarEntregaLoteRequest(
        data_entrega=date.today(),
        nota_fiscal="NF-1234",
        itens=[
            EntregaItemLote(id_pedido=1, quantidade=Decimal('100.00')) # Entrega Total
        ]
    )
    
    # 3. Executa
    resultado = repo.registrar_entrega_lote(lote_req)
    
    # 4. Asserções (Verificações)
    assert resultado['sucesso'] is True
    assert resultado['qtd_itens'] == 1
    
    # Verifica se o cursor executou o UPDATE correto
    cursor = mock_db_conn.cursor.return_value
    
    # O SQL esperado deve atualizar para 100.00 entregues e status 'Entregue'
    # Args esperados: (nova_qtd, novo_status, id_pedido)
    args_chamada = cursor.execute.call_args[0]
    sql_executado = args_chamada[0]
    params_executados = args_chamada[1]
    
    assert "UPDATE pedidos" in sql_executado
    assert params_executados[0] == Decimal('100.00') # Nova Quantidade Entregue
    assert params_executados[1] == 'Entregue'        # Novo Status
    assert params_executados[2] == 1                 # ID do Pedido
    
    # Verifica se houve commit
    mock_db_conn.commit.assert_called_once()

def test_registrar_entrega_lote_parcial(mock_db_conn, pedido_pendente):
    """
    Testa se o status muda para 'Entrega Parcial' quando a quantidade é menor que o total.
    """
    repo = PedidoRepository(mock_db_conn)
    repo.get_by_id = MagicMock(return_value=pedido_pendente)
    
    lote_req = RegistrarEntregaLoteRequest(
        data_entrega=date.today(),
        nota_fiscal="NF-1234",
        itens=[
            EntregaItemLote(id_pedido=1, quantidade=Decimal('50.00')) # Metade
        ]
    )
    
    repo.registrar_entrega_lote(lote_req)
    
    cursor = mock_db_conn.cursor.return_value
    params = cursor.execute.call_args[0][1]
    
    assert params[0] == Decimal('50.00')      # 0 + 50
    assert params[1] == 'Entrega Parcial'     # Status esperado

def test_registrar_entrega_lote_rollback_erro(mock_db_conn):
    """
    Testa se o banco faz ROLLBACK se um dos itens falhar (ex: pedido não encontrado).
    """
    repo = PedidoRepository(mock_db_conn)
    
    # Simula que o get_by_id retorna None (Pedido não existe)
    repo.get_by_id = MagicMock(return_value=None)
    
    lote_req = RegistrarEntregaLoteRequest(
        data_entrega=date.today(),
        nota_fiscal="NF-ERRO",
        itens=[
            EntregaItemLote(id_pedido=999, quantidade=Decimal('10.00'))
        ]
    )
    
    # Verifica se lança a exceção esperada
    with pytest.raises(ValueError) as excinfo:
        repo.registrar_entrega_lote(lote_req)
    
    assert "Pedido ID 999 não encontrado" in str(excinfo.value)
    
    # A verificação mais importante: ROLLBACK foi chamado?
    mock_db_conn.rollback.assert_called_once()
    # Commit NÃO deve ser chamado
    mock_db_conn.commit.assert_not_called()

# --- Teste de Integração da Rota (Simulado com client do FastAPI) ---

from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

# Mock para pular autenticação e banco na rota
@pytest.fixture
def client_override_auth(mock_db_conn):
    """
    Cria um cliente de teste que ignora a autenticação real e injeta o mock de banco.
    """
    # Sobrescreve a dependência de get_db
    from app.core.database import get_db
    app.dependency_overrides[get_db] = lambda: mock_db_conn
    
    # Cria um usuário fake e token para passar no @require_access_level
    # (A implementação real depende de como você configurou o override nos seus outros testes)
    # Aqui vamos assumir que o token é válido
    return TestClient(app)

def test_rota_entrega_lote_endpoint(client_override_auth, mock_db_conn):
    """
    Testa se o endpoint responde 200 OK e chama o repositório corretamente.
    """
    # Mockando o repositório dentro da rota (patching a classe)
    with patch("app.routers.pedido_router.PedidoRepository") as MockRepoClass:
        mock_repo_instance = MockRepoClass.return_value
        mock_repo_instance.registrar_entrega_lote.return_value = {"sucesso": True, "qtd_itens": 2}
        
        # Simula usuário logado (token fake)
        # Se sua segurança valida o token no banco, precisaria mockar o get_current_user também
        # Vou assumir um mock do get_current_user para simplificar
        from app.core.security import get_current_user
        from app.models.user_model import User
        
        app.dependency_overrides[get_current_user] = lambda: User(id=1, username="admin", nivel_acesso=1, ativo=True, password_hash="hash")

        payload = {
            "data_entrega": "2023-10-27",
            "nota_fiscal": "NF-TESTE-API",
            "itens": [
                {"id_pedido": 1, "quantidade": 10},
                {"id_pedido": 2, "quantidade": 20}
            ]
        }
        
        response = client_override_auth.post("/api/pedidos/entrega-lote", json=payload)
        
        assert response.status_code == 200
        assert response.json()["mensagem"] == "Entregas registradas com sucesso!"
        
        # Verifica se o repositório foi chamado com os dados certos
        mock_repo_instance.registrar_entrega_lote.assert_called_once()