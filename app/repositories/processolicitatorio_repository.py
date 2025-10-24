import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from app.models.processolicitatorio_model import Processolicitatorio
from app.schemas.processolicitatorio_schema import ProcessolicitatorioRequest

class ProcessolicitatorioRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    #Criar (C)
    def create(self, Processolicitatorio_req: ProcessolicitatorioRequest) -> Processolicitatorio:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO processoslicitatorios (numero) 
                VALUES (%s) 
                RETURNING * """
            cursor.execute(sql, (Processolicitatorio_req.numero,))
            
            new_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            return Processolicitatorio(
                id=new_data['id'],
                numero=new_data['numero'],
            )
        finally:
            if cursor:
                cursor.close()

    #Listar (R)
    def get_all(self) -> list[Processolicitatorio]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
        
            sql = "SELECT * FROM processoslicitatorios ORDER BY numero"
        
            cursor.execute(sql)
        
            all_data = cursor.fetchall()
        
            return [Processolicitatorio(
                id=row['id'], 
                numero=row['numero']
            )
            for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Processolicitatorio | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM processoslicitatorios WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return Processolicitatorio(id=data['id'], numero=data['numero'])
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #Atualizar (U)
    def update(self, id: int, Processolicitatorio_req: ProcessolicitatorioRequest) -> Processolicitatorio | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE processoslicitatorios 
                SET numero = %s 
                WHERE id = %s
                RETURNING *
            """
            cursor.execute(sql, (Processolicitatorio_req.numero, id))
            updated_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            if updated_data:
                return Processolicitatorio(
                    id=updated_data['id'],
                    numero=updated_data['numero'],
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
            
            sql = "DELETE FROM processoslicitatorios WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()
                
    #Busca pelo nome exato                
    def get_by_nome(self, numero: str) -> Processolicitatorio | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM processoslicitatorios WHERE numero = %s"
            cursor.execute(sql, (numero,))
            data = cursor.fetchone()
            if data:
                return Processolicitatorio(id=data['id'], numero=data['numero'])
            return None
        finally:
            if cursor:
                cursor.close()

    #Cria a categoria se não existir
    def get_or_create(self, numero: str) -> Processolicitatorio:
        instrumento = self.get_by_nome(numero) 
        if instrumento:
            return instrumento
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO processoslicitatorios (numero) VALUES (%s) RETURNING *"
            cursor.execute(sql, (numero,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            return Processolicitatorio(id=new_data['id'], numero=new_data['numero'])

        except psycopg2.IntegrityError:
            self.db_conn.rollback()
            cursor.close() 
            categoria_existente = self.get_by_nome(numero)
            if categoria_existente:
                return categoria_existente
            else:
                raise Exception(f"Erro inesperado ao buscar categoria '{numero}' após conflito de inserção.")

        finally:
            if cursor and not cursor.closed:
                cursor.close()   