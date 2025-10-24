import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from app.models.numeromodalidade_model import Numeromodalidade
from app.schemas.numeromodalidade_schema import NumeromodalidadeRequest

class NumeromodalidadeRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    #Criar (C)
    def create(self, Numeromodalidade_req: NumeromodalidadeRequest) -> Numeromodalidade:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO numeromodalidade (numero_ano) 
                VALUES (%s) 
                RETURNING * """
            cursor.execute(sql, (Numeromodalidade_req.numero_ano,))
            
            new_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            return Numeromodalidade(
                id=new_data['id'],
                numero_ano=new_data['numero_ano'],
            )
        finally:
            if cursor:
                cursor.close()

    #Listar (R)
    def get_all(self) -> list[Numeromodalidade]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
        
            sql = "SELECT * FROM numeromodalidade ORDER BY numero_ano"
        
            cursor.execute(sql)
        
            all_data = cursor.fetchall()
        
            return [Numeromodalidade(
                id=row['id'], 
                numero_ano=row['numero_ano']
            )
            for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Numeromodalidade | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM numeromodalidade WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return Numeromodalidade(id=data['id'], numero_ano=data['numero_ano'])
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #Atualizar (U)
    def update(self, id: int, Numeromodalidade_req: NumeromodalidadeRequest) -> Numeromodalidade | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE numeromodalidade 
                SET numero_ano = %s 
                WHERE id = %s
                RETURNING *
            """
            cursor.execute(sql, (Numeromodalidade_req.numero_ano, id))
            updated_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            if updated_data:
                return Numeromodalidade(
                    id=updated_data['id'],
                    numero_ano=updated_data['numero_ano'],
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
            
            sql = "DELETE FROM numeromodalidade WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()
                
    #Busca pelo nome exato                
    def get_by_nome(self, numero_ano: str) -> Numeromodalidade | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM numeromodalidade WHERE numero_ano = %s"
            cursor.execute(sql, (numero_ano,))
            data = cursor.fetchone()
            if data:
                return Numeromodalidade(id=data['id'], numero_ano=data['numero_ano'])
            return None
        finally:
            if cursor:
                cursor.close()

    #Cria a categoria se não existir
    def get_or_create(self, numero_ano: str) -> Numeromodalidade:
        instrumento = self.get_by_nome(numero_ano) 
        if instrumento:
            return instrumento
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO numeromodalidade (numero_ano) VALUES (%s) RETURNING *"
            cursor.execute(sql, (numero_ano,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            return Numeromodalidade(id=new_data['id'], numero_ano=new_data['numero_ano'])

        except psycopg2.IntegrityError:
            self.db_conn.rollback()
            cursor.close() 
            categoria_existente = self.get_by_nome(numero_ano)
            if categoria_existente:
                return categoria_existente
            else:
                raise Exception(f"Erro inesperado ao buscar categoria '{numero_ano}' após conflito de inserção.")

        finally:
            if cursor and not cursor.closed:
                cursor.close()   