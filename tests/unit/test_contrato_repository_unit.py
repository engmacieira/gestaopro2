import pytest
from datetime import date
from unittest.mock import MagicMock
from psycopg2 import OperationalError, errors
from app.repositories.contrato_repository import ContratoRepository
from app.schemas.contrato_schema import ContratoCreateRequest, ContratoUpdateRequest
from app.schemas.fornecedor_schema import FornecedorRequest

@pytest.fixture
def mock_db_session():
    mock_conn = MagicMock()
    mock_conn.commit.return_value = None
    mock_conn.rollback.return_value = None
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return mock_conn

@pytest.fixture
def contrato_repo(mock_db_session):
    repo = ContratoRepository(mock_db_session)
    
    repo.categoria_repo = MagicMock()
    repo.categoria_repo.get_by_nome.return_value = MagicMock(id=1)
    
    repo.instrumento_repo = MagicMock()
    repo.instrumento_repo.get_by_nome.return_value = MagicMock(id=1)
    
    repo.modalidade_repo = MagicMock()
    repo.modalidade_repo.get_by_nome.return_value = MagicMock(id=1)
    
    repo.numeromodalidade_repo = MagicMock()
    repo.numeromodalidade_repo.get_by_numero_ano.return_value = MagicMock(id=1)
    
    repo.processolicitatorio_repo = MagicMock()
    repo.processolicitatorio_repo.get_by_numero.return_value = MagicMock(id=1)
    
    return repo

@pytest.fixture
def valid_contrato_request():
    return ContratoCreateRequest(
        numero_contrato="123/2023",
        data_inicio=date(2023, 1, 1),
        data_fim=date(2023, 12, 31),
        categoria_nome="Serviços",
        instrumento_nome="Contrato",
        modalidade_nome="Pregão",
        numero_modalidade_str="001/2023",
        processo_licitatorio_numero="PROC-123",
        fornecedor=FornecedorRequest(nome="Forn Teste", cpf_cnpj="000", email="a@a.com", telefone="111")
    )

def mock_execute_failure(mock_db_session, exception_type):
    mock_cursor = mock_db_session.cursor.return_value.__enter__.return_value
    mock_cursor.execute.side_effect = exception_type("Simulated DB Error")
    mock_db_session.cursor.return_value.execute.side_effect = exception_type("Simulated DB Error")

def test_get_all_contratos_db_error(contrato_repo, mock_db_session):
    """Verifica se get_all captura o erro e retorna lista vazia."""
    mock_execute_failure(mock_db_session, OperationalError)
    resultado = contrato_repo.get_all()
    assert resultado == []
    print("\n[Contrato Repo] PASSOU: get_all tratou erro retornando [].")

def test_create_contrato_integrity_error(contrato_repo, mock_db_session, valid_contrato_request):
    """Verifica se create lida com erro de integridade (ex: numero_contrato duplicado)."""
    mock_execute_failure(mock_db_session, errors.UniqueViolation)
    
    with pytest.raises(errors.UniqueViolation):
        contrato_repo.create(valid_contrato_request)
        
    mock_db_session.rollback.assert_called_once()
    print("\n[Contrato Repo] PASSOU: create tratou UniqueViolation (Rollback).")

def test_get_contrato_by_id_db_error(contrato_repo, mock_db_session):
    """Verifica se get_by_id trata erros de banco retornando None."""
    mock_execute_failure(mock_db_session, OperationalError)
    resultado = contrato_repo.get_by_id(id=999)
    assert resultado is None
    print("\n[Contrato Repo] PASSOU: get_by_id tratou erro retornando None.")

def test_update_contrato_db_error(contrato_repo, mock_db_session):
    """Verifica se update lida com erro de banco."""
    contrato_repo.get_by_id = MagicMock(return_value=MagicMock())
    
    mock_execute_failure(mock_db_session, OperationalError)
    
    update_req = ContratoUpdateRequest(numero_contrato="Novo Num")
    
    with pytest.raises(OperationalError):
        contrato_repo.update(id=1, contrato_req=update_req)

    mock_db_session.rollback.assert_called_once()
    print("\n[Contrato Repo] PASSOU: update tratou OperationalError (Rollback).")

def test_delete_contrato_db_error(contrato_repo, mock_db_session):
    """Verifica se delete lida com erro de banco."""
    contrato_repo.get_by_id = MagicMock(return_value=MagicMock())
    mock_execute_failure(mock_db_session, OperationalError)

    with pytest.raises(OperationalError):
        contrato_repo.delete(id=1)

    mock_db_session.rollback.assert_called_once()
    print("\n[Contrato Repo] PASSOU: delete tratou OperationalError (Rollback).")