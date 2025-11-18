import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from psycopg2 import IntegrityError
from app.routers.agente_router import create_agente 
from app.schemas.agente_schema import AgenteRequest 

def test_create_conflict():
    req = AgenteRequest(nome="Duplo") 
    with patch("app.routers.agente_router.AgenteRepository") as MockRepo: 
        MockRepo.return_value.create.side_effect = IntegrityError("Duplicado")
        
        with pytest.raises(HTTPException) as exc:
            create_agente(req, MagicMock(), MagicMock())
        assert exc.value.status_code == 409

def test_update_not_found():
    req = AgenteRequest(nome="Novo") 
    with patch("app.routers.agente_router.AgenteRepository") as MockRepo: 
        MockRepo.return_value.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            from app.routers.agente_router import update_agente 
            update_agente(99, req, MagicMock(), MagicMock())
        assert exc.value.status_code == 404