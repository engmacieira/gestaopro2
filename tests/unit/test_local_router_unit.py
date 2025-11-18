import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from psycopg2 import IntegrityError
from app.routers.local_router import create_local 
from app.schemas.local_schema import LocalRequest 

def test_create_conflict():
    req = LocalRequest(descricao="Duplo") 
    with patch("app.routers.local_router.LocalRepository") as MockRepo: 
        MockRepo.return_value.create.side_effect = IntegrityError("Duplicado")
        
        with pytest.raises(HTTPException) as exc:
            create_local(req, MagicMock(), MagicMock())
        assert exc.value.status_code == 409

def test_update_not_found():
    req = LocalRequest(descricao="Novo") 
    with patch("app.routers.local_router.LocalRepository") as MockRepo: 
        MockRepo.return_value.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            from app.routers.local_router import update_local 
            update_local(99, req, MagicMock(), MagicMock())
        assert exc.value.status_code == 404