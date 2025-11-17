import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
import logging
from app.models.local_model import Local 
from app.schemas.local_schema import LocalRequest 

logger = logging.getLogger(__name__)

class LocalRepository: 
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    def _map_row_to_model(self, row: DictCursor | None) -> Local | None:
        if not row:
            return None
        try:
            return Local(id=row['id'], descricao=row['descricao'])
        except KeyError as e:
            logger.error(f"Erro de mapeamento Local: Coluna '{e}' não encontrada.")
            return None

    def create(self, local_req: LocalRequest) -> Local:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO locaisentrega (descricao) VALUES (%s) RETURNING *"
            cursor.execute(sql, (local_req.descricao,)) 
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_local = self._map_row_to_model(new_data)
            if not new_local:
                logger.error("Falha ao mapear dados do local recém-criado.")
                raise Exception("Falha ao mapear dados do local recém-criado.")

            logger.info(f"Local criado com ID {new_local.id}: '{new_local.descricao}'")
            return new_local

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao criar local (Req: {local_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_all(self) -> list[Local]:
        cursor = None
        locais = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM locaisentrega ORDER BY descricao" 
            cursor.execute(sql)
            all_data = cursor.fetchall()
            locais = [self._map_row_to_model(row) for row in all_data if row]
            locais = [loc for loc in locais if loc is not None]
            return locais
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar locais: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> Local | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM locaisentrega WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar local por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def update(self, id: int, local_req: LocalRequest) -> Local | None:
        cursor = None
        local_antigo = self.get_by_id(id)
        if not local_antigo:
             logger.warning(f"Tentativa de atualizar local ID {id} falhou (não encontrado).")
             return None

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE locaisentrega SET descricao = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (local_req.descricao, id))
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_local = self._map_row_to_model(updated_data)
            if updated_local:
                logger.info(f"Local ID {id} atualizado de '{local_antigo.descricao}' para '{updated_local.descricao}'.")
            return updated_local

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            if isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao atualizar local ID {id} para '{local_req.descricao}'. Descrição duplicada?")
            else:
                 logger.exception(f"Erro inesperado ao atualizar local ID {id} (Req: {local_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        local_para_deletar = self.get_by_id(id)
        if not local_para_deletar:
             logger.warning(f"Tentativa de deletar local ID {id} falhou (não encontrado).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM locaisentrega WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"Local ID {id} ('{local_para_deletar.descricao}') deletado.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error:
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar local ID {id} ('{local_para_deletar.descricao}'). Vinculado a AOCS.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar local ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()

    def get_by_descricao(self, descricao: str) -> Local | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM locaisentrega WHERE descricao = %s"
            cursor.execute(sql, (descricao,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar local por descricao ('{descricao}'): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_or_create(self, descricao: str) -> Local:
        try:
            local_obj = self.get_by_descricao(descricao)
            if local_obj:
                return local_obj
        except Exception:
             logger.exception(f"Erro ao buscar local '{descricao}' em get_or_create. Tentando criar...")

        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO locaisentrega (descricao) VALUES (%s) RETURNING *"
            cursor.execute(sql, (descricao,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            new_local = self._map_row_to_model(new_data)
            if not new_local:
                 log_message = f"Falha ao mapear local '{descricao}' recém-criado em get_or_create."
                 logger.error(log_message)
                 raise Exception(log_message)

            logger.info(f"Local '{descricao}' não encontrado/erro na busca, criado novo com ID {new_local.id}.")
            return new_local

        except psycopg2.IntegrityError:
            logging.warning(f"IntegrityError ao criar local '{descricao}' em get_or_create. Já existe. Buscando novamente.")
            self.db_conn.rollback()
            if cursor and not cursor.closed: cursor.close()

            local_existente = self.get_by_descricao(descricao) 
            if local_existente:
                return local_existente
            else:
                log_message = f"Erro INESPERADO ao buscar local '{descricao}' após conflito de inserção."
                logger.exception(log_message)
                raise Exception(log_message)

        except (Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             logger.exception(f"Erro inesperado na criação do get_or_create para local '{descricao}': {error}")
             raise
        finally:
            if cursor and not cursor.closed:
                cursor.close()