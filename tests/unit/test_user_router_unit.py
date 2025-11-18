import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from psycopg2 import IntegrityError
from app.routers.user_router import create_user, update_user
from app.schemas.user_schema import UserCreateRequest, UserUpdateRequest
from app.models.user_model import User

@pytest.fixture
def mock_db_conn(): return MagicMock()

def test_create_user_conflict(mock_db_conn):
    req = UserCreateRequest(username="duplo", password="12345678", nivel_acesso=1)
    
    with patch("app.routers.user_router.UserRepository") as MockRepo:
        mock_instance = MockRepo.return_value
        mock_instance.get_by_username.return_value = None
        mock_instance.create.side_effect = IntegrityError("Duplicado")
        
        with pytest.raises(HTTPException) as exc:
            create_user(req, mock_db_conn)
        assert exc.value.status_code == 400 

def test_update_user_not_found(mock_db_conn):
    req = UserUpdateRequest(username="novo")
    with patch("app.routers.user_router.UserRepository") as MockRepo:
        MockRepo.return_value.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            update_user(99, req, mock_db_conn)
        assert exc.value.status_code == 404