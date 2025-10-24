import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from app.models.dotacao_models import Dotacao
from app.schemas.dotacao_schema import DotacaoRequest

class DotacaoRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    #Criar (C)
    def create(self, Dotacao_req: DotacaoRequest) -> Dotacao:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO dotacao (info_orcamentaria) 
                VALUES (%s) 
                RETURNING * """
            cursor.execute(sql, (Dotacao_req.info_orcamentaria,))
            
            new_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            return Dotacao(
                id=new_data['id'],
                info_orcamentaria=new_data['info_orcamentaria'],
            )
        finally:
            if cursor:
                cursor.close()

    #Listar (R)
    def get_all(self) -> list[Dotacao]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
        
            sql = "SELECT * FROM dotacao ORDER BY info_orcamentaria"
        
            cursor.execute(sql)
        
            all_data = cursor.fetchall()
        
            return [Dotacao(
                id=row['id'], 
                info_orcamentaria=row['info_orcamentaria']
            )
            for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Dotacao | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM dotacao WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return Dotacao(id=data['id'], info_orcamentaria=data['info_orcamentaria'])
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #Atualizar (U)
    def update(self, id: int, Dotacao_req: DotacaoRequest) -> Dotacao | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE dotacao 
                SET info_orcamentaria = %s 
                WHERE id = %s
                RETURNING *
            """
            cursor.execute(sql, (Dotacao_req.info_orcamentaria, id))
            updated_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            if updated_data:
                return Dotacao(
                    id=updated_data['id'],
                    info_orcamentaria=updated_data['info_orcamentaria'],
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
            
            sql = "DELETE FROM dotacao WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()
                
    #Busca pelo nome exato                
    def get_by_nome(self, info_orcamentaria: str) -> Dotacao | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM dotacao WHERE info_orcamentaria = %s"
            cursor.execute(sql, (info_orcamentaria,))
            data = cursor.fetchone()
            if data:
                return Dotacao(id=data['id'], info_orcamentaria=data['info_orcamentaria'])
            return None
        finally:
            if cursor:
                cursor.close()

    #Cria a categoria se não existir
    def get_or_create(self, info_orcamentaria: str) -> Dotacao:
        instrumento = self.get_by_info_orcamentaria(info_orcamentaria) 
        if instrumento:
            return instrumento
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO dotacao (info_orcamentaria) VALUES (%s) RETURNING *"
            cursor.execute(sql, (info_orcamentaria,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            return Dotacao(id=new_data['id'], info_orcamentaria=new_data['info_orcamentaria'])

        except psycopg2.IntegrityError:
            self.db_conn.rollback()
            cursor.close() 
            categoria_existente = self.get_by_info_orcamentaria(info_orcamentaria)
            if categoria_existente:
                return categoria_existente
            else:
                raise Exception(f"Erro inesperado ao buscar dotacao '{info_orcamentaria}' após conflito de inserção.")

        finally:
            if cursor and not cursor.closed:
                cursor.close()   