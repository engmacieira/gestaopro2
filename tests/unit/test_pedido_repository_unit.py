import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from psycopg2 import OperationalError, errors
from app.repositories.pedido_repository import PedidoRepository
from app.schemas.pedido_schema import PedidoCreateRequest

@pytest.fixture
def mock_db_session():
    mock_conn = MagicMock()
    mock_conn.commit.return_value = None
    mock_conn.rollback.return_value = None
    mock_conn.cursor.return_value.__enter__.return_value = MagicMock()
    return mock_conn

@pytest.fixture
def pedido_repo(mock_db_session):
    repo = PedidoRepository(mock_db_session)
    repo.item_repo = MagicMock()
    repo.aocs_repo = MagicMock()
    return repo

def test_create_pedido_saldo_insuficiente(pedido_repo, mock_db_session):
    req = PedidoCreateRequest(item_contrato_id=1, quantidade_pedida=Decimal("30.0"))
    
    pedido_repo.aocs_repo.get_by_id.return_value = MagicMock(id=1)
    mock_item = MagicMock(id=1, ativo=True, quantidade=Decimal("100.0"))
    pedido_repo.item_repo.get_by_id.return_value = mock_item
    
    pedido_repo.get_total_requested_quantity = MagicMock(return_value=Decimal("80.0"))

    with pytest.raises(ValueError) as exc:
        pedido_repo.create(id_aocs=1, pedido_create_req=req)
    
    assert "excede o saldo disponível" in str(exc.value)
    print("\n[Pedido Repo] PASSOU: Bloqueou pedido com saldo insuficiente.")

def test_create_pedido_db_error(pedido_repo, mock_db_session):
    req = PedidoCreateRequest(item_contrato_id=1, quantidade_pedida=Decimal("10.0"))
    
    pedido_repo.aocs_repo.get_by_id.return_value = MagicMock()
    pedido_repo.item_repo.get_by_id.return_value = MagicMock(ativo=True, quantidade=Decimal("1000"))
    pedido_repo.get_total_requested_quantity = MagicMock(return_value=Decimal("0"))

    mock_cursor = mock_db_session.cursor.return_value
    mock_cursor.execute.side_effect = OperationalError("DB Morto")

    with pytest.raises(OperationalError):
        pedido_repo.create(1, req)
    mock_db_session.rollback.assert_called()