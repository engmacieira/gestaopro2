import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from psycopg2 import IntegrityError
from app.routers.instrumento_router import create_instrumento 
from app.schemas.instrumento_schema import InstrumentoRequest 

def test_create_conflict():
    req = InstrumentoRequest(nome="Duplo") 
    with patch("app.routers.instrumento_router.InstrumentoRepository") as MockRepo: 
        MockRepo.return_value.create.side_effect = IntegrityError("Duplicado")
        
        with pytest.raises(HTTPException) as exc:
            create_instrumento(req, MagicMock(), MagicMock())
        assert exc.value.status_code == 409

def test_update_not_found():
    req = InstrumentoRequest(nome="Novo") 
    with patch("app.routers.instrumento_router.InstrumentoRepository") as MockRepo: 
        MockRepo.return_value.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            from app.routers.instrumento_router import update_instrumento 
            update_instrumento(99, req, MagicMock(), MagicMock())
        assert exc.value.status_code == 404