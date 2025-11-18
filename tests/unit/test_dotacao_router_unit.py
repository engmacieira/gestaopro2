import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from psycopg2 import IntegrityError
from app.routers.dotacao_router import create_dotacao 
from app.schemas.dotacao_schema import DotacaoRequest 

def test_create_conflict():
    req = DotacaoRequest(info_orcamentaria="Duplo") 
    with patch("app.routers.dotacao_router.DotacaoRepository") as MockRepo: 
        MockRepo.return_value.create.side_effect = IntegrityError("Duplicado")
        
        with pytest.raises(HTTPException) as exc:
            create_dotacao(req, MagicMock(), MagicMock())
        assert exc.value.status_code == 409

def test_update_not_found():
    req = DotacaoRequest(info_orcamentaria="Novo") 
    with patch("app.routers.dotacao_router.DotacaoRepository") as MockRepo: 
        MockRepo.return_value.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            from app.routers.dotacao_router import update_dotacao 
            update_dotacao(99, req, MagicMock(), MagicMock())
        assert exc.value.status_code == 404