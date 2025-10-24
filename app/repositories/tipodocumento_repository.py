import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from app.models.tipodocumento_model import Tipodocumento
from app.schemas.tipodocumento_schema import TipodocumentoRequest

class TipodocumentoRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    #Criar (C)
    def create(self, Tipodocumento_req: TipodocumentoRequest) -> Tipodocumento:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO tipos_documento (nome) 
                VALUES (%s) 
                RETURNING * """
            cursor.execute(sql, (Tipodocumento_req.nome,))
            
            new_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            return Tipodocumento(
                id=new_data['id'],
                nome=new_data['nome'],
            )
        finally:
            if cursor:
                cursor.close()

    #Listar (R)
    def get_all(self) -> list[Tipodocumento]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
        
            sql = "SELECT * FROM tipos_documento ORDER BY nome"
        
            cursor.execute(sql)
        
            all_data = cursor.fetchall()
        
            return [Tipodocumento(
                id=row['id'], 
                nome=row['nome']
            )
            for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Tipodocumento | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM tipos_documento WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return Tipodocumento(id=data['id'], nome=data['nome'])
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #Atualizar (U)
    def update(self, id: int, Tipodocumento_req: TipodocumentoRequest) -> Tipodocumento | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE tipos_documento 
                SET nome = %s 
                WHERE id = %s
                RETURNING *
            """
            cursor.execute(sql, (Tipodocumento_req.nome, id))
            updated_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            if updated_data:
                return Tipodocumento(
                    id=updated_data['id'],
                    nome=updated_data['nome'],
                )
            
            return None
        finally:
            if cursor:
                cursor.close()

    #Excluir (D)
    def delete(self, id: int) -> bool:
        cursor = None
        try:
            cursor = self.db_conn.cursor()
            
            sql = "DELETE FROM tipos_documento WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()
                
    #Busca pelo nome exato                
    def get_by_nome(self, nome: str) -> Tipodocumento | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM tipos_documento WHERE nome = %s"
            cursor.execute(sql, (nome,))
            data = cursor.fetchone()
            if data:
                return Tipodocumento(id=data['id'], nome=data['nome'])
            return None
        finally:
            if cursor:
                cursor.close()

    #Cria a categoria se não existir
    def get_or_create(self, nome: str) -> Tipodocumento:
        instrumento = self.get_by_nome(nome) 
        if instrumento:
            return instrumento
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO tipos_documento (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            return Tipodocumento(id=new_data['id'], nome=new_data['nome'])

        except psycopg2.IntegrityError:
            self.db_conn.rollback()
            cursor.close() 
            categoria_existente = self.get_by_nome(nome)
            if categoria_existente:
                return categoria_existente
            else:
                raise Exception(f"Erro inesperado ao buscar tiposdocumentos '{nome}' após conflito de inserção.")

        finally:
            if cursor and not cursor.closed:
                cursor.close()   