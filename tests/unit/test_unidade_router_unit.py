import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from psycopg2 import IntegrityError
from app.routers.unidade_router import create_unidade 
from app.schemas.unidade_schema import UnidadeRequest 

def test_create_conflict():
    req = UnidadeRequest(nome="Duplo") 
    with patch("app.routers.unidade_router.UnidadeRepository") as MockRepo: 
        MockRepo.return_value.create.side_effect = IntegrityError("Duplicado")
        
        with pytest.raises(HTTPException) as exc:
            create_unidade(req, MagicMock(), MagicMock())
        assert exc.value.status_code == 409

def test_update_not_found():
    req = UnidadeRequest(nome="Novo") 
    with patch("app.routers.unidade_router.UnidadeRepository") as MockRepo: 
        MockRepo.return_value.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            from app.routers.unidade_router import update_unidade 
            update_unidade(99, req, MagicMock(), MagicMock())
        assert exc.value.status_code == 404