import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from app.models.unidade_model import Unidade
from app.schemas.unidade_schema import UnidadeRequest

class UnidadeRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    #Criar (C)
    def create(self, Unidade_req: UnidadeRequest) -> Unidade:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO unidadesrequisitantes (nome) 
                VALUES (%s) 
                RETURNING * """
            cursor.execute(sql, (Unidade_req.nome,))
            
            new_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            return Unidade(
                id=new_data['id'],
                nome=new_data['nome'],
            )
        finally:
            if cursor:
                cursor.close()

    #Listar (R)
    def get_all(self) -> list[Unidade]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
        
            sql = "SELECT * FROM unidadesrequisitantes ORDER BY nome"
        
            cursor.execute(sql)
        
            all_data = cursor.fetchall()
        
            return [Unidade(
                id=row['id'], 
                nome=row['nome']
            )
            for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Unidade | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM unidadesrequisitantes WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return Unidade(id=data['id'], nome=data['nome'])
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #Atualizar (U)
    def update(self, id: int, Unidade_req: UnidadeRequest) -> Unidade | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE unidadesrequisitantes 
                SET nome = %s 
                WHERE id = %s
                RETURNING *
            """
            cursor.execute(sql, (Unidade_req.nome, id))
            updated_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            if updated_data:
                return Unidade(
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
            
            sql = "DELETE FROM unidadesrequisitantes WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()
                
    #Busca pelo nome exato                
    def get_by_nome(self, nome: str) -> Unidade | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM unidadesrequisitantes WHERE nome = %s"
            cursor.execute(sql, (nome,))
            data = cursor.fetchone()
            if data:
                return Unidade(id=data['id'], nome=data['nome'])
            return None
        finally:
            if cursor:
                cursor.close()

    #Cria a categoria se não existir
    def get_or_create(self, nome: str) -> Unidade:
        instrumento = self.get_by_nome(nome) 
        if instrumento:
            return instrumento
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO unidadesrequisitantes (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            return Unidade(id=new_data['id'], nome=new_data['nome'])

        except psycopg2.IntegrityError:
            self.db_conn.rollback()
            cursor.close() 
            categoria_existente = self.get_by_nome(nome)
            if categoria_existente:
                return categoria_existente
            else:
                raise Exception(f"Erro inesperado ao buscar unidades '{nome}' após conflito de inserção.")

        finally:
            if cursor and not cursor.closed:
                cursor.close()   