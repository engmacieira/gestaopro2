import pytest
from unittest.mock import MagicMock
from psycopg2 import OperationalError, errors
from app.repositories.categoria_repository import CategoriaRepository 
from app.schemas.categoria_schema import CategoriaRequest 

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
def repo(mock_db_session):
    return CategoriaRepository(mock_db_session) 

def test_create_db_error(repo, mock_db_session):
    req = CategoriaRequest(nome="Teste") 
    mock_db_session.cursor.return_value.execute.side_effect = OperationalError("Erro")
    with pytest.raises(OperationalError):
        repo.create(req)
    mock_db_session.rollback.assert_called()

def test_get_all_db_error(repo, mock_db_session):
    mock_db_session.cursor.return_value.execute.side_effect = OperationalError("Erro")
    res = repo.get_all()
    assert res == [] 

def test_update_db_error(repo, mock_db_session):
    repo.get_by_id = MagicMock(return_value=MagicMock()) 
    mock_db_session.cursor.return_value.execute.side_effect = OperationalError("Erro")
    with pytest.raises(OperationalError):
        repo.update(1, CategoriaRequest(nome="Novo")) 
    mock_db_session.rollback.assert_called()

def test_delete_db_error(repo, mock_db_session):
    repo.get_by_id = MagicMock(return_value=MagicMock())
    mock_db_session.cursor.return_value.execute.side_effect = OperationalError("Erro")
    with pytest.raises(OperationalError):
        repo.delete(1)
    mock_db_session.rollback.assert_called()