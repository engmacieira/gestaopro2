import pytest
import os
from unittest.mock import MagicMock
from psycopg2 import OperationalError
from app.core.database import _get_db_connection, get_db

def mock_psycopg2_connect(monkeypatch):
    def mock_connect(*args, **kwargs):
        raise OperationalError("Simulated DB connection failure")
    
    monkeypatch.setattr("psycopg2.connect", mock_connect)

def test_get_db_connection_falha_conexao(monkeypatch):
    mock_psycopg2_connect(monkeypatch)
    
    monkeypatch.delitem(os.environ, 'DATABASE_URL', raising=False) 
    
    monkeypatch.setitem(os.environ, 'DB_HOST', 'invalid_host')
    monkeypatch.setitem(os.environ, 'DB_NAME', 'invalid_db')
    monkeypatch.setitem(os.environ, 'DB_USER', 'invalid_user')
    monkeypatch.setitem(os.environ, 'DB_PASSWORD', 'invalid_pass')
    
    with pytest.raises(OperationalError) as excinfo:
        _get_db_connection()
    
    assert "Simulated DB connection failure" in str(excinfo.value)
    print("\n[Pytest] PASSOU: Falha de conexão tratada corretamente.")

def test_get_db_connection_sem_db_host(monkeypatch):
    monkeypatch.delitem(os.environ, 'DATABASE_URL', raising=False)
    
    monkeypatch.delitem(os.environ, 'DB_HOST', raising=False)
    
    monkeypatch.delitem(os.environ, 'DB_NAME', raising=False)
    monkeypatch.delitem(os.environ, 'DB_USER', raising=False)
    monkeypatch.delitem(os.environ, 'DB_PASSWORD', raising=False)

    with pytest.raises(ValueError) as excinfo:
        _get_db_connection()
        
    assert "Erro: Variável de ambiente DB_HOST não definida." in str(excinfo.value)
    print("\n[Pytest] PASSOU: Falta de DB_HOST tratada corretamente.")
    
def test_get_db_falha_na_conexao(monkeypatch):
    def mock_get_db_connection():
        raise OperationalError("Simulated DB connection failure in get_db")
    
    monkeypatch.setattr("app.core.database._get_db_connection", mock_get_db_connection)
    
    with pytest.raises(OperationalError) as excinfo:
        list(get_db())
        
    assert "Simulated DB connection failure in get_db" in str(excinfo.value)
    print("\n[Pytest] PASSOU: get_db trata falha na conexão.")