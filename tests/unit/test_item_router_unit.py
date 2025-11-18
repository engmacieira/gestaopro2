import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from psycopg2 import IntegrityError
from app.routers.item_router import create_item, update_item, delete_item, get_item_by_id
from app.schemas.item_schema import ItemRequest
from app.schemas.descricao_item_schema import DescricaoItemRequest
from app.models.user_model import User
from decimal import Decimal

@pytest.fixture
def mock_user():
    return User(id=1, username="test_admin", password_hash="hash", nivel_acesso=1, ativo=True)

@pytest.fixture
def mock_item_request():
    return ItemRequest(
        numero_item=99,
        marca="Marca Mock",
        unidade_medida="UN",
        quantidade=Decimal("10.0"),
        valor_unitario=Decimal("100.0"),
        contrato_nome="Contrato Mock",
        descricao=DescricaoItemRequest(descricao="Descrição Mock")
    )

@pytest.fixture
def mock_db_conn():
    return MagicMock()

def test_create_item_value_error_returns_400(mock_item_request, mock_db_conn, mock_user):
    with patch("app.routers.item_router.ItemRepository") as MockRepo:
        mock_instance = MockRepo.return_value
        mock_instance.create.side_effect = ValueError("Contrato não encontrado")

        with pytest.raises(HTTPException) as excinfo:
            create_item(item_req=mock_item_request, db_conn=mock_db_conn, current_user=mock_user)
        
        assert excinfo.value.status_code == 400
        assert "Contrato não encontrado" in str(excinfo.value.detail)
        print("\n[Router Unit] PASSOU: ValueError convertido para 400.")

def test_create_item_integrity_error_returns_409(mock_item_request, mock_db_conn, mock_user):
    with patch("app.routers.item_router.ItemRepository") as MockRepo:
        mock_instance = MockRepo.return_value
        mock_instance.create.side_effect = IntegrityError("Chave duplicada")

        with pytest.raises(HTTPException) as excinfo:
            create_item(item_req=mock_item_request, db_conn=mock_db_conn, current_user=mock_user)
        
        assert excinfo.value.status_code == 409
        assert "Erro de integridade" in str(excinfo.value.detail)
        print("\n[Router Unit] PASSOU: IntegrityError convertido para 409.")

def test_update_item_not_found_returns_404(mock_item_request, mock_db_conn, mock_user):
    with patch("app.routers.item_router.ItemRepository") as MockRepo:
        mock_instance = MockRepo.return_value
        mock_instance.get_by_id.return_value = None 

        with pytest.raises(HTTPException) as excinfo:
            update_item(id=999, item_req=mock_item_request, db_conn=mock_db_conn, current_user=mock_user)
        
        assert excinfo.value.status_code == 404
        print("\n[Router Unit] PASSOU: Item inexistente no Update retorna 404.")

def test_delete_item_integrity_error_returns_409(mock_db_conn, mock_user):
    with patch("app.routers.item_router.ItemRepository") as MockRepo:
        mock_instance = MockRepo.return_value
        mock_instance.get_by_id.return_value = MagicMock() 
        mock_instance.delete.side_effect = IntegrityError("Violação de FK")

        with pytest.raises(HTTPException) as excinfo:
            delete_item(id=1, db_conn=mock_db_conn, current_user=mock_user)
        
        assert excinfo.value.status_code == 409
        assert "Este Item está vinculado a Pedidos" in str(excinfo.value.detail)
        print("\n[Router Unit] PASSOU: Erro ao deletar item vinculado retorna 409.")

def test_delete_item_generic_exception_returns_500(mock_db_conn, mock_user):
    with patch("app.routers.item_router.ItemRepository") as MockRepo:
        mock_instance = MockRepo.return_value
        mock_instance.get_by_id.return_value = MagicMock()
        mock_instance.delete.side_effect = Exception("Erro fatal desconhecido")

        with pytest.raises(HTTPException) as excinfo:
            delete_item(id=1, db_conn=mock_db_conn, current_user=mock_user)
        
        assert excinfo.value.status_code == 500
        assert "Erro interno do servidor" in str(excinfo.value.detail)
        print("\n[Router Unit] PASSOU: Exception genérica retorna 500.")