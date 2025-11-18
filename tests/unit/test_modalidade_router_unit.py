import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from psycopg2 import IntegrityError
from app.routers.modalidade_router import create_modalidade 
from app.schemas.modalidade_schema import ModalidadeRequest 

def test_create_conflict():
    req = ModalidadeRequest(nome="Duplo") 
    with patch("app.routers.modalidade_router.ModalidadeRepository") as MockRepo: 
        MockRepo.return_value.create.side_effect = IntegrityError("Duplicado")
        
        with pytest.raises(HTTPException) as exc:
            create_modalidade(req, MagicMock(), MagicMock())
        assert exc.value.status_code == 409

def test_update_not_found():
    req = ModalidadeRequest(nome="Novo") 
    with patch("app.routers.modalidade_router.ModalidadeRepository") as MockRepo: 
        MockRepo.return_value.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            from app.routers.modalidade_router import update_modalidade 
            update_modalidade(99, req, MagicMock(), MagicMock())
        assert exc.value.status_code == 404