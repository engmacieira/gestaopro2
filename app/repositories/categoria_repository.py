import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
import logging 
from app.models.categoria_model import Categoria
from app.schemas.categoria_schema import CategoriaRequest

logger = logging.getLogger(__name__)

class CategoriaRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    def _map_row_to_model(self, row: DictCursor | None) -> Categoria | None:
        if not row:
            return None
        try:
            return Categoria(id=row['id'], nome=row['nome'], ativo=row['ativo'])
        except KeyError as e:
            logger.error(f"Erro de mapeamento Categoria: Coluna '{e}' não encontrada.")
            return None

    def create(self, categoria_req: CategoriaRequest) -> Categoria:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO Categorias (nome) VALUES (%s) RETURNING *" 
            cursor.execute(sql, (categoria_req.nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_categoria = self._map_row_to_model(new_data)
            if not new_categoria:
                logger.error("Falha ao mapear dados da categoria recém-criada.")
                raise Exception("Falha ao mapear dados da categoria recém-criada.")

            logger.info(f"Categoria criada com ID {new_categoria.id}: '{new_categoria.nome}'")
            return new_categoria

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao criar categoria (Req: {categoria_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_all(self, mostrar_inativos: bool = False) -> list[Categoria]:
        cursor = None
        categorias = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM Categorias" 
            if not mostrar_inativos:
                sql += " WHERE ativo = TRUE"
            sql += " ORDER BY nome"
            cursor.execute(sql)
            all_data = cursor.fetchall()
            categorias = [self._map_row_to_model(row) for row in all_data if row]
            categorias = [cat for cat in categorias if cat is not None]
            return categorias
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar categorias (Inativos: {mostrar_inativos}): {error}")
             return []
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> Categoria | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM Categorias WHERE id = %s" 
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar categoria por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def update(self, id: int, categoria_req: CategoriaRequest) -> Categoria | None:
        cursor = None
        categoria_antiga = self.get_by_id(id)
        if not categoria_antiga:
             logger.warning(f"Tentativa de atualizar categoria ID {id} falhou (não encontrada).")
             return None 

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE Categorias SET nome = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (categoria_req.nome, id))
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_categoria = self._map_row_to_model(updated_data)
            if updated_categoria:
                 logger.info(f"Categoria ID {id} atualizada de '{categoria_antiga.nome}' para '{updated_categoria.nome}'.")
            else:
                 logger.error(f"Falha ao mapear categoria ID {id} após atualização bem sucedida.")
            return updated_categoria

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao atualizar categoria ID {id} (Req: {categoria_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def set_active_status(self, id: int, status: bool) -> Categoria | None:
        cursor = None
        categoria_original = self.get_by_id(id)
        if not categoria_original:
            logger.warning(f"Tentativa de alterar status da categoria ID {id} falhou (não encontrada).")
            return None

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE Categorias SET ativo = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (status, id))
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_categoria = self._map_row_to_model(updated_data)
            if updated_categoria:
                action = "ativada" if status else "desativada"
                logger.info(f"Categoria ID {id} ('{updated_categoria.nome}') foi {action}.")
            else:
                logger.error(f"Falha ao mapear categoria ID {id} após alteração de status.")
            return updated_categoria

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao alterar status da categoria ID {id} para {status}: {error}")
            raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        categoria_para_deletar = self.get_by_id(id)
        if not categoria_para_deletar:
             logger.warning(f"Tentativa de deletar categoria ID {id} falhou (não encontrada).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM Categorias WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"Categoria ID {id} ('{categoria_para_deletar.nome}') deletada.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error:
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar categoria ID {id} ('{categoria_para_deletar.nome}'). Vinculada a Contratos.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar categoria ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()

    def get_by_nome(self, nome: str, buscar_inativos: bool = False) -> Categoria | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM Categorias WHERE nome = %s" 
            params = [nome]
            if not buscar_inativos:
                sql += " AND ativo = TRUE"
            cursor.execute(sql, params)
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar categoria por nome ('{nome}'): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_or_create(self, nome: str) -> Categoria:
        try:
            categoria = self.get_by_nome(nome, buscar_inativos=False)
            if categoria:
                return categoria
        except Exception:
             logger.exception(f"Erro ao buscar categoria '{nome}' em get_or_create. Tentando criar...")

        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO Categorias (nome) VALUES (%s) RETURNING *" 
            cursor.execute(sql, (nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            new_categoria = self._map_row_to_model(new_data)
            if not new_categoria:
                 log_message = f"Falha ao mapear categoria '{nome}' recém-criada em get_or_create."
                 logger.error(log_message)
                 raise Exception(log_message)

            logger.info(f"Categoria '{nome}' não encontrada/inativa, criada nova com ID {new_categoria.id}.")
            return new_categoria

        except psycopg2.IntegrityError:
            logging.warning(f"IntegrityError ao criar categoria '{nome}' em get_or_create. Já existe. Buscando novamente.")
            self.db_conn.rollback()
            if cursor and not cursor.closed: cursor.close()

            categoria_existente = self.get_by_nome(nome, buscar_inativos=True)
            if categoria_existente:
                logger.info(f"Categoria '{nome}' encontrada (pode estar inativa) após conflito de inserção.")
                return categoria_existente
            else:
                log_message = f"Erro INESPERADO: Categoria '{nome}' não encontrada após conflito de inserção em get_or_create."
                logger.exception(log_message)
                raise Exception(log_message)

        except (Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             logger.exception(f"Erro inesperado na criação do get_or_create para categoria '{nome}': {error}")
             raise
        finally:
            if cursor and not cursor.closed:
                cursor.close()
    
    def change_status(self, id: int, status: bool) -> Categoria | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE categorias SET ativo = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (status, id))
            
            updated_row = cursor.fetchone()
            if not updated_row:
                return None 
                
            self.db_conn.commit()
            
            return self._map_row_to_model(updated_row)

        except (Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             logger.exception(f"Erro ao alterar status da categoria ID {id} para {status}: {error}")
             raise
        finally:
            if cursor:
                cursor.close()