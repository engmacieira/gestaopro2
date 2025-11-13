import pytest
import os
import psycopg2
from psycopg2.extras import DictCursor
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.test')

from app.main import app 
from app.core.database import get_db

@pytest.fixture(scope="session")
def db_conn_test():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL não definida no .env.test")
        
    conn = None
    try:
        conn = psycopg2.connect(db_url, cursor_factory=DictCursor)
        print("\n[Pytest] Conectado ao banco de dados de TESTE.")
        yield conn
    finally:
        if conn:
            conn.close()
            print("\n[Pytest] Desconectado do banco de dados de TESTE.")

# tests/conftest.py

@pytest.fixture(scope="function")
def db_session(db_conn_test):    
    try:
        with db_conn_test.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE pedidos RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE ci_pagamento RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE anexos RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE itenscontrato RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE aocs RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE contratos RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE usuarios RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE categorias RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE instrumentocontratual RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE modalidade RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE numeromodalidade RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE processoslicitatorios RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE unidadesrequisitantes RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE locaisentrega RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE agentesresponsaveis RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE dotacao RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE tipos_documento RESTART IDENTITY CASCADE;")
        db_conn_test.commit() 
        print("\n[Pytest] Banco de teste limpo (TRUNCATE).")

    except Exception as e:
        print(f"\n[Pytest] FALHA AO LIMPAR O BANCO: {e}")
        db_conn_test.rollback()
        raise

    yield db_conn_test

@pytest.fixture(scope="function")
def test_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()