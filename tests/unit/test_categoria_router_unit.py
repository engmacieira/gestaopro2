import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from psycopg2 import IntegrityError
from app.routers.categoria_router import create_categoria 
from app.schemas.categoria_schema import CategoriaRequest 

def test_create_conflict():
    req = CategoriaRequest(nome="Duplo") 
    with patch("app.routers.categoria_router.CategoriaRepository") as MockRepo: 
        MockRepo.return_value.create.side_effect = IntegrityError("Duplicado")
        
        with pytest.raises(HTTPException) as exc:
            create_categoria(req, MagicMock(), MagicMock())
        assert exc.value.status_code == 409

def test_update_not_found():
    req = CategoriaRequest(nome="Novo") 
    with patch("app.routers.categoria_router.CategoriaRepository") as MockRepo: 
        MockRepo.return_value.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            from app.routers.categoria_router import update_categoria 
            update_categoria(99, req, MagicMock(), MagicMock())
        assert exc.value.status_code == 404