import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from app.models.local_model import Local
from app.schemas.local_schema import LocalRequest

class LocalRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    #Criar (C)
    def create(self, Local_req: LocalRequest) -> Local:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO locaisentrega (descricao) 
                VALUES (%s) 
                RETURNING * """
            cursor.execute(sql, (Local_req.descricao,))
            
            new_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            return Local(
                id=new_data['id'],
                descricao=new_data['descricao'],
            )
        finally:
            if cursor:
                cursor.close()

    #Listar (R)
    def get_all(self) -> list[Local]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
        
            sql = "SELECT * FROM locaisentrega ORDER BY descricao"
        
            cursor.execute(sql)
        
            all_data = cursor.fetchall()
        
            return [Local(
                id=row['id'], 
                descricao=row['descricao']
            )
            for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Local | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM locaisentrega WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return Local(id=data['id'], descricao=data['descricao'])
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #Atualizar (U)
    def update(self, id: int, Local_req: LocalRequest) -> Local | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE locaisentrega 
                SET descricao = %s 
                WHERE id = %s
                RETURNING *
            """
            cursor.execute(sql, (Local_req.descricao, id))
            updated_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            if updated_data:
                return Local(
                    id=updated_data['id'],
                    descricao=updated_data['descricao'],
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
            
            sql = "DELETE FROM locaisentrega WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()
                
    #Busca pelo nome exato                
    def get_by_nome(self, descricao: str) -> Local | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM locaisentrega WHERE descricao = %s"
            cursor.execute(sql, (descricao,))
            data = cursor.fetchone()
            if data:
                return Local(id=data['id'], descricao=data['descricao'])
            return None
        finally:
            if cursor:
                cursor.close()

    #Cria a categoria se não existir
    def get_or_create(self, descricao: str) -> Local:
        instrumento = self.get_by_descricao(descricao) 
        if instrumento:
            return instrumento
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO locaisentrega (descricao) VALUES (%s) RETURNING *"
            cursor.execute(sql, (descricao,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            return Local(id=new_data['id'], descricao=new_data['descricao'])

        except psycopg2.IntegrityError:
            self.db_conn.rollback()
            cursor.close() 
            categoria_existente = self.get_by_descricao(descricao)
            if categoria_existente:
                return categoria_existente
            else:
                raise Exception(f"Erro inesperado ao buscar locais '{descricao}' após conflito de inserção.")

        finally:
            if cursor and not cursor.closed:
                cursor.close()   