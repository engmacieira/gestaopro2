import os
import psycopg2
from psycopg2.extras import DictCursor

def _get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        if os.environ.get('RENDER') == 'true':
            return psycopg2.connect(database_url, sslmode='require', cursor_factory=DictCursor)
        else:
            return psycopg2.connect(database_url, cursor_factory=DictCursor)
    
    db_host = os.environ.get("DB_HOST")
    db_name = os.environ.get("DB_NAME")
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASSWORD")

    if not db_host:
        raise ValueError("Erro: Variável de ambiente DB_HOST não definida. Verifique seu .env")
        
    return psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_pass,
        cursor_factory=DictCursor
    )

def get_db():
    conn = None
    try:
        conn = _get_db_connection()
        yield conn  
    finally:
        if conn:
            conn.close() 