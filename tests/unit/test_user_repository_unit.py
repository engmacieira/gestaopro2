import pytest
from unittest.mock import MagicMock
from psycopg2 import OperationalError, IntegrityError
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreateRequest, UserUpdateRequest

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
def user_repo(mock_db_session):
    return UserRepository(mock_db_session)

def mock_execute_failure(mock_db_session, exception_type):
    mock_db_session.cursor.return_value.__enter__.return_value.execute.side_effect = exception_type("Simulated Error")
    mock_db_session.cursor.return_value.execute.side_effect = exception_type("Simulated Error")

def test_create_user_db_error(user_repo, mock_db_session):
    req = UserCreateRequest(username="test", password="12345678", nivel_acesso=1, ativo=True)
    mock_execute_failure(mock_db_session, OperationalError)
    
    with pytest.raises(OperationalError):
        user_repo.create(req)
    mock_db_session.rollback.assert_called()

def test_get_by_username_db_error(user_repo, mock_db_session):
    mock_execute_failure(mock_db_session, OperationalError)
    res = user_repo.get_by_username("test")
    assert res is None 

def test_update_user_db_error(user_repo, mock_db_session):
    req = UserUpdateRequest(username="new_name")
    user_repo.get_by_id = MagicMock(return_value=MagicMock())
    
    mock_execute_failure(mock_db_session, OperationalError)
    
    with pytest.raises(OperationalError):
        user_repo.update(1, req)
    mock_db_session.rollback.assert_called()

def test_reset_password_db_error(user_repo, mock_db_session):
    mock_execute_failure(mock_db_session, OperationalError)
    res = user_repo.reset_password(1, "new_hash")
    assert res is False 
    mock_db_session.rollback.assert_called()