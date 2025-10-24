import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from app.models.categoria_model import Categoria
from app.schemas.categoria_schema import CategoriaRequest

class CategoriaRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    #Criar
    def create(self, categoria_req: CategoriaRequest) -> Categoria:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO Categorias (nome) 
                VALUES (%s) 
                RETURNING * """
            cursor.execute(sql, (categoria_req.nome,))
            
            new_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            return Categoria(
                id=new_data['id'],
                nome=new_data['nome'],
                ativo=new_data['ativo']
            )
        finally:
            if cursor:
                cursor.close()

    #Listar
    def get_all(self, mostrar_inativos: bool = False) -> list[Categoria]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM Categorias"
            if not mostrar_inativos:
                sql += " WHERE ativo = TRUE"
            sql += " ORDER BY nome"
            
            cursor.execute(sql)
            all_data = cursor.fetchall()
            
            return [
                Categoria(id=row['id'], nome=row['nome'], ativo=row['ativo']) 
                for row in all_data
            ]
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Categoria | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM Categorias WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return Categoria(id=data['id'], nome=data['nome'], ativo=data['ativo'])
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #Atualizar
    def update(self, id: int, categoria_req: CategoriaRequest) -> Categoria | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE Categorias 
                SET nome = %s 
                WHERE id = %s
                RETURNING *
            """
            cursor.execute(sql, (categoria_req.nome, id))
            updated_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            if updated_data:
                return Categoria(
                    id=updated_data['id'],
                    nome=updated_data['nome'],
                    ativo=updated_data['ativo']
                )
            
            return None
        finally:
            if cursor:
                cursor.close()

    #Excluir
    def delete(self, id: int) -> bool:
        cursor = None
        try:
            cursor = self.db_conn.cursor()
            
            sql = "DELETE FROM Categorias WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()

    #Busca pelo nome exato                
    def get_by_nome(self, nome: str) -> Categoria | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM Categorias WHERE nome = %s AND ativo = TRUE"
            cursor.execute(sql, (nome,))
            data = cursor.fetchone()
            if data:
                return Categoria(id=data['id'], nome=data['nome'], ativo=data['ativo'])
            return None
        finally:
            if cursor:
                cursor.close()

    #Cria a categoria se não existir
    def get_or_create(self, nome: str) -> Categoria:
        instrumento = self.get_by_nome(nome) 
        if instrumento:
            return instrumento
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO Categorias (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            return Categoria(id=new_data['id'], nome=new_data['nome'], ativo=new_data['ativo'])

        except psycopg2.IntegrityError:
            self.db_conn.rollback()
            cursor.close() 
            categoria_existente = self.get_by_nome(nome)
            if categoria_existente:
                return categoria_existente
            else:
                raise Exception(f"Erro inesperado ao buscar categoria '{nome}' após conflito de inserção.")

        finally:
            if cursor and not cursor.closed:
                cursor.close()