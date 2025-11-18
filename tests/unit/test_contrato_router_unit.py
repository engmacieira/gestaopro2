import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from psycopg2 import IntegrityError
from app.routers.contrato_router import create_contrato, update_contrato, delete_contrato
from app.schemas.contrato_schema import ContratoCreateRequest, ContratoUpdateRequest
from app.schemas.fornecedor_schema import FornecedorRequest
from app.models.user_model import User

@pytest.fixture
def mock_user():
    return User(id=1, username="test_admin", password_hash="hash", nivel_acesso=1, ativo=True)

@pytest.fixture
def mock_db_conn():
    return MagicMock()

@pytest.fixture
def mock_contrato_request():
    return ContratoCreateRequest(
        numero_contrato="123/2023",
        data_inicio=date(2023, 1, 1),
        data_fim=date(2023, 12, 31),
        categoria_nome="Cat",
        instrumento_nome="Inst",
        modalidade_nome="Mod",
        numero_modalidade_str="001",
        processo_licitatorio_numero="Proc",
        fornecedor=FornecedorRequest(nome="Forn", cpf_cnpj="000")
    )

def test_create_contrato_value_error_returns_400(mock_contrato_request, mock_db_conn, mock_user):
    with patch("app.routers.contrato_router.ContratoRepository") as MockRepo:
        mock_instance = MockRepo.return_value
        mock_instance.create.side_effect = ValueError("Categoria não encontrada")

        with pytest.raises(HTTPException) as excinfo:
            create_contrato(contrato_req=mock_contrato_request, db_conn=mock_db_conn, current_user=mock_user)
        
        assert excinfo.value.status_code == 400
        assert "Categoria não encontrada" in str(excinfo.value.detail)
        print("\n[Contrato Router] PASSOU: ValueError -> 400.")

def test_create_contrato_integrity_error_returns_409(mock_contrato_request, mock_db_conn, mock_user):
    with patch("app.routers.contrato_router.ContratoRepository") as MockRepo:
        mock_instance = MockRepo.return_value
        mock_instance.create.side_effect = IntegrityError("Duplicado")

        with pytest.raises(HTTPException) as excinfo:
            create_contrato(contrato_req=mock_contrato_request, db_conn=mock_db_conn, current_user=mock_user)
        
        assert excinfo.value.status_code == 409
        assert "já existe" in str(excinfo.value.detail)
        print("\n[Contrato Router] PASSOU: IntegrityError -> 409.")

def test_update_contrato_not_found_returns_404(mock_db_conn, mock_user):
    with patch("app.routers.contrato_router.ContratoRepository") as MockRepo:
        mock_instance = MockRepo.return_value
        mock_instance.get_by_id.return_value = None 

        with pytest.raises(HTTPException) as excinfo:
            update_contrato(id=999, contrato_req=ContratoUpdateRequest(), db_conn=mock_db_conn, current_user=mock_user)
        
        assert excinfo.value.status_code == 404
        print("\n[Contrato Router] PASSOU: Update Not Found -> 404.")

def test_delete_contrato_integrity_error_returns_409(mock_db_conn, mock_user):
    with patch("app.routers.contrato_router.ContratoRepository") as MockRepo:
        mock_instance = MockRepo.return_value
        mock_instance.get_by_id.return_value = MagicMock() 
        mock_instance.delete.side_effect = IntegrityError("FK Violation")

        with pytest.raises(HTTPException) as excinfo:
            delete_contrato(id=1, db_conn=mock_db_conn, current_user=mock_user)
        
        assert excinfo.value.status_code == 409
        assert "vinculados" in str(excinfo.value.detail)
        print("\n[Contrato Router] PASSOU: Delete com Vínculo -> 409.")

def test_delete_contrato_generic_exception_returns_500(mock_db_conn, mock_user):
    with patch("app.routers.contrato_router.ContratoRepository") as MockRepo:
        mock_instance = MockRepo.return_value
        mock_instance.get_by_id.return_value = MagicMock()
        mock_instance.delete.side_effect = Exception("Erro Fatal")

        with pytest.raises(HTTPException) as excinfo:
            delete_contrato(id=1, db_conn=mock_db_conn, current_user=mock_user)
        
        assert excinfo.value.status_code == 500
        print("\n[Contrato Router] PASSOU: Exception Genérica -> 500.")