# tests/conftest.py

import pytest
import os
os.environ["TESTING"] = "true" 
import psycopg2
from psycopg2.extras import DictCursor
from fastapi.testclient import TestClient # <--- VOLTAMOS PARA O TestClient
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.test')

from app.main import app 
from app.core.database import get_db, _get_db_connection

# Imports necessários para a fixture de autenticação
from app.core.security import create_access_token 
from app.models.user_model import User 
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreateRequest


@pytest.fixture(scope="session")
def db_conn_test():
    """
    Cria uma conexão-mãe com o banco de TESTE para toda a sessão de testes.
    """
    conn = None
    try:
        conn = _get_db_connection()
        print("\n[Pytest] Conectado ao banco de dados de TESTE.")
        yield conn
    except Exception as e:
        print(f"\n[Pytest] FALHA AO CONECTAR NO BANCO DE TESTE: {e}")
        print("Verifique seu .env.test e se o banco 'gestaopro_test' existe e tem as tabelas.")
        raise
    finally:
        if conn:
            conn.close()
            print("\n[Pytest] Desconectado do banco de dados de TESTE.")

@pytest.fixture(scope="function")
def db_session(db_conn_test):
    """
    Garante isolamento total do teste limpando o banco de dados ANTES de cada teste
    usando TRUNCATE.
    """    
    try:
        with db_conn_test.cursor() as cursor:
            # Limpa tabelas em ordem de dependência
            cursor.execute("TRUNCATE TABLE pedidos RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE ci_pagamento RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE anexos RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE itenscontrato RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE aocs RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE contratos RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE usuarios RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE categorias RESTART IDENTITY CASCADE;")
            
            # Limpa o resto das tabelas de domínio
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
def test_client(db_session): # <--- MUDANÇA: 'def' (não mais 'async def')
    """
    Cria um TestClient síncrono para testar a aplicação.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass # A limpeza é feita pelo TRUNCATE

    app.dependency_overrides[get_db] = override_get_db
    
    # MUDANÇA: Voltamos a usar o TestClient
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def admin_auth_headers(db_session): 
    """
    Fixture global de autenticação (sem alterações).
    """
    repo = UserRepository(db_session)
    user_data = UserCreateRequest(
        username="test_admin_user",
        password="password123",
        nivel_acesso=1, 
        ativo=True
    )
    try:
        admin_user = repo.create(user_data)
        db_session.commit() 
    except Exception as e:
        db_session.rollback()
        admin_user = repo.get_by_username("test_admin_user")
    
    token = create_access_token(admin_user)
    
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def user_auth_headers(db_session): 
    """
    Fixture global de autenticação para utilizador-padrão.
    """
    repo = UserRepository(db_session)
    user_data = UserCreateRequest(
        username="test_user_user",
        password="password123",
        nivel_acesso=3
    )
    # Tenta criar o utilizador
    try:
        user = repo.create(user_data)
    except psycopg2.IntegrityError:
        db_session.rollback()
        user = repo.get_by_username("test_user_user")
    
    # Garantia de que o utilizador existe
    assert user is not None, "Falha ao criar ou obter o 'test_user_user' na fixture"

    # --- A CORREÇÃO ---
    # Chamada igual à da fixture do admin
    access_token = create_access_token(user) 
    
    return {"Authorization": f"Bearer {access_token}"}