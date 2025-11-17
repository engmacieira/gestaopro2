import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
import logging
from app.models.dotacao_model import Dotacao
from app.schemas.dotacao_schema import DotacaoRequest

logger = logging.getLogger(__name__)

class DotacaoRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    def _map_row_to_model(self, row: DictCursor | None) -> Dotacao | None:
        if not row:
            return None
        try:
            return Dotacao(id=row['id'], info_orcamentaria=row['info_orcamentaria'])
        except KeyError as e:
            logger.error(f"Erro de mapeamento Dotacao: Coluna '{e}' não encontrada.")
            return None

    def create(self, dotacao_req: DotacaoRequest) -> Dotacao:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO dotacao (info_orcamentaria) VALUES (%s) RETURNING *"
            cursor.execute(sql, (dotacao_req.info_orcamentaria,))
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_dotacao = self._map_row_to_model(new_data)
            if not new_dotacao:
                logger.error("Falha ao mapear dados da dotação recém-criada.")
                raise Exception("Falha ao mapear dados da dotação recém-criada.")

            logger.info(f"Dotação criada com ID {new_dotacao.id}: '{new_dotacao.info_orcamentaria}'")
            return new_dotacao

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao criar dotação (Req: {dotacao_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_all(self) -> list[Dotacao]:
        cursor = None
        dotacoes = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM dotacao ORDER BY info_orcamentaria"
            cursor.execute(sql)
            all_data = cursor.fetchall()
            dotacoes = [self._map_row_to_model(row) for row in all_data if row]
            dotacoes = [d for d in dotacoes if d is not None]
            return dotacoes
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar dotações: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> Dotacao | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM dotacao WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar dotação por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def update(self, id: int, dotacao_req: DotacaoRequest) -> Dotacao | None:
        cursor = None
        dotacao_antiga = self.get_by_id(id) 
        if not dotacao_antiga:
             logger.warning(f"Tentativa de atualizar dotação ID {id} falhou (não encontrada).")
             return None

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE dotacao SET info_orcamentaria = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (dotacao_req.info_orcamentaria, id))
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_dotacao = self._map_row_to_model(updated_data)
            if updated_dotacao:
                logger.info(f"Dotação ID {id} atualizada de '{dotacao_antiga.info_orcamentaria}' para '{updated_dotacao.info_orcamentaria}'.")
            return updated_dotacao

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao atualizar dotação ID {id} (Req: {dotacao_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        dotacao_para_deletar = self.get_by_id(id)
        if not dotacao_para_deletar:
             logger.warning(f"Tentativa de deletar dotação ID {id} falhou (não encontrada).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM dotacao WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"Dotação ID {id} ('{dotacao_para_deletar.info_orcamentaria}') deletada.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error:
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar dotação ID {id} ('{dotacao_para_deletar.info_orcamentaria}'). Vinculada a AOCS/CI.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar dotação ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()

    def get_by_info_orcamentaria(self, info_orcamentaria: str) -> Dotacao | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM dotacao WHERE info_orcamentaria = %s"
            cursor.execute(sql, (info_orcamentaria,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar dotação por info ('{info_orcamentaria}'): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_or_create(self, info_orcamentaria: str) -> Dotacao:
        try:
            dotacao = self.get_by_info_orcamentaria(info_orcamentaria) 
            if dotacao:
                return dotacao
        except Exception:
             logger.exception(f"Erro ao buscar dotação '{info_orcamentaria}' em get_or_create. Tentando criar...")

        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO dotacao (info_orcamentaria) VALUES (%s) RETURNING *"
            cursor.execute(sql, (info_orcamentaria,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            new_dotacao = self._map_row_to_model(new_data)
            if not new_dotacao:
                 log_message = f"Falha ao mapear dotação '{info_orcamentaria}' recém-criada em get_or_create."
                 logger.error(log_message)
                 raise Exception(log_message)

            logger.info(f"Dotação '{info_orcamentaria}' não encontrada/erro na busca, criada nova com ID {new_dotacao.id}.")
            return new_dotacao

        except psycopg2.IntegrityError:
            logging.warning(f"IntegrityError ao criar dotação '{info_orcamentaria}' em get_or_create. Já existe. Buscando novamente.")
            self.db_conn.rollback()
            if cursor and not cursor.closed: cursor.close()

            dotacao_existente = self.get_by_info_orcamentaria(info_orcamentaria) 
            if dotacao_existente:
                return dotacao_existente
            else:
                log_message = f"Erro INESPERADO ao buscar dotação '{info_orcamentaria}' após conflito de inserção."
                logger.exception(log_message)
                raise Exception(log_message)

        except (Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             logger.exception(f"Erro inesperado na criação do get_or_create para dotação '{info_orcamentaria}': {error}")
             raise
        finally:
            if cursor and not cursor.closed:
                cursor.close()