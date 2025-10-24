import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from app.models.agente_model import Agente
from app.schemas.agente_schema import AgenteRequest

class AgenteRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    #Criar (C)
    def create(self, Agente_req: AgenteRequest) -> Agente:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO agentesresponsaveis (nome) 
                VALUES (%s) 
                RETURNING * """
            cursor.execute(sql, (Agente_req.nome,))
            
            new_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            return Agente(
                id=new_data['id'],
                nome=new_data['nome'],
            )
        finally:
            if cursor:
                cursor.close()

    #Listar (R)
    def get_all(self) -> list[Agente]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
        
            sql = "SELECT * FROM agentesresponsaveis ORDER BY nome"
        
            cursor.execute(sql)
        
            all_data = cursor.fetchall()
        
            return [Agente(
                id=row['id'], 
                nome=row['nome']
            )
            for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Agente | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM agentesresponsaveis WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return Agente(id=data['id'], nome=data['nome'])
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #Atualizar (U)
    def update(self, id: int, Agente_req: AgenteRequest) -> Agente | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE agentesresponsaveis 
                SET nome = %s 
                WHERE id = %s
                RETURNING *
            """
            cursor.execute(sql, (Agente_req.nome, id))
            updated_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            if updated_data:
                return Agente(
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
            
            sql = "DELETE FROM agentesresponsaveis WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()
                
    #Busca pelo nome exato                
    def get_by_nome(self, nome: str) -> Agente | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM agentesresponsaveis WHERE nome = %s"
            cursor.execute(sql, (nome,))
            data = cursor.fetchone()
            if data:
                return Agente(id=data['id'], nome=data['nome'])
            return None
        finally:
            if cursor:
                cursor.close()

    #Cria a categoria se não existir
    def get_or_create(self, nome: str) -> Agente:
        instrumento = self.get_by_nome(nome) 
        if instrumento:
            return instrumento
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO agentesresponsaveis (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            return Agente(id=new_data['id'], nome=new_data['nome'])

        except psycopg2.IntegrityError:
            self.db_conn.rollback()
            cursor.close() 
            categoria_existente = self.get_by_nome(nome)
            if categoria_existente:
                return categoria_existente
            else:
                raise Exception(f"Erro inesperado ao buscar agentes '{nome}' após conflito de inserção.")

        finally:
            if cursor and not cursor.closed:
                cursor.close()   