import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from psycopg2 import OperationalError, errors
from app.repositories.item_repository import ItemRepository
from app.schemas.item_schema import ItemRequest
from app.schemas.descricao_item_schema import DescricaoItemRequest

@pytest.fixture
def mock_db_session():
    mock_conn = MagicMock()
    
    mock_conn.commit.return_value = None
    mock_conn.rollback.return_value = None

    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor 
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor 

    return mock_conn

@pytest.fixture
def item_repo(mock_db_session):
    repo = ItemRepository(mock_db_session)
    repo.contrato_repo = MagicMock()
    mock_contrato = MagicMock()
    mock_contrato.id = 1
    repo.contrato_repo.get_by_numero_contrato.return_value = mock_contrato
    return repo

@pytest.fixture
def valid_item_request():
    descricao = DescricaoItemRequest(descricao="Item de Teste")
    return ItemRequest(
        numero_item=1,
        marca="Marca Teste",
        unidade_medida="UN",
        quantidade=Decimal("10.0"),
        valor_unitario=Decimal("50.0"),
        contrato_nome="Contrato 123",
        descricao=descricao
    )

def mock_execute_failure(mock_db_session, exception_type):
    mock_cursor = mock_db_session.cursor.return_value.__enter__.return_value
    
    mock_cursor.execute.side_effect = exception_type("Simulated DB Error")
    
    mock_db_session.cursor.return_value.execute.side_effect = exception_type("Simulated DB Error")

def test_get_all_items_db_error(item_repo, mock_db_session):
    mock_execute_failure(mock_db_session, OperationalError)

    resultado = item_repo.get_all()

    assert resultado == []
    print("\n[Pytest] PASSOU: get_all tratou erro retornando lista vazia.")

def test_create_item_integrity_error(item_repo, mock_db_session, valid_item_request):
    mock_execute_failure(mock_db_session, errors.UniqueViolation)

    with pytest.raises(errors.UniqueViolation):
        item_repo.create(valid_item_request)
        
    mock_db_session.rollback.assert_called_once()
    print("\n[Pytest] PASSOU: create tratou UniqueViolation e chamou rollback.")

def test_get_item_by_id_db_error(item_repo, mock_db_session):
    mock_execute_failure(mock_db_session, OperationalError)

    resultado = item_repo.get_by_id(id=999)

    assert resultado is None
    print("\n[Pytest] PASSOU: get_by_id tratou erro retornando None.")

def test_update_item_db_error(item_repo, mock_db_session, valid_item_request):
    item_repo.get_by_id = MagicMock(return_value=MagicMock())

    mock_execute_failure(mock_db_session, OperationalError)

    with pytest.raises(OperationalError):
        item_repo.update(id=1, item_req=valid_item_request)

    mock_db_session.rollback.assert_called_once()
    print("\n[Pytest] PASSOU: update tratou OperationalError e chamou rollback.")

def test_delete_item_db_error(item_repo, mock_db_session):
    item_repo.get_by_id = MagicMock(return_value=MagicMock())

    mock_execute_failure(mock_db_session, OperationalError)

    with pytest.raises(OperationalError):
        item_repo.delete(id=1)

    mock_db_session.rollback.assert_called_once()
    print("\n[Pytest] PASSOU: delete tratou OperationalError e chamou rollback.")