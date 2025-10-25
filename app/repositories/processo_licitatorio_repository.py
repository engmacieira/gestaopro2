import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
import logging
from app.models.processo_licitatorio_model import ProcessoLicitatorio 
from app.schemas.processo_licitatorio_schema import ProcessoLicitatorioRequest 

logger = logging.getLogger(__name__)

class ProcessoLicitatorioRepository: 
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    def _map_row_to_model(self, row: DictCursor | None) -> ProcessoLicitatorio | None:
        if not row:
            return None
        try:
            return ProcessoLicitatorio(id=row['id'], numero=row['numero'])
        except KeyError as e:
            logger.error(f"Erro de mapeamento ProcessoLicitatorio: Coluna '{e}' não encontrada.")
            return None

    def create(self, proc_req: ProcessoLicitatorioRequest) -> ProcessoLicitatorio:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO processoslicitatorios (numero) VALUES (%s) RETURNING *"
            cursor.execute(sql, (proc_req.numero,)) 
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_proc = self._map_row_to_model(new_data)
            if not new_proc:
                logger.error("Falha ao mapear dados do processo licitatório recém-criado.")
                raise Exception("Falha ao mapear dados do processo licitatório recém-criado.")

            logger.info(f"Processo Licitatório criado com ID {new_proc.id}: '{new_proc.numero}'")
            return new_proc

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao criar processo licitatório (Req: {proc_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_all(self) -> list[ProcessoLicitatorio]:
        cursor = None
        processos = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM processoslicitatorios ORDER BY numero" 
            cursor.execute(sql)
            all_data = cursor.fetchall()
            processos = [self._map_row_to_model(row) for row in all_data if row]
            processos = [p for p in processos if p is not None]
            return processos
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar processos licitatórios: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> ProcessoLicitatorio | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM processoslicitatorios WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar processo licitatório por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def update(self, id: int, proc_req: ProcessoLicitatorioRequest) -> ProcessoLicitatorio | None:
        cursor = None
        proc_antigo = self.get_by_id(id)
        if not proc_antigo:
             logger.warning(f"Tentativa de atualizar processo licitatório ID {id} falhou (não encontrado).")
             return None

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE processoslicitatorios SET numero = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (proc_req.numero, id)) 
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_proc = self._map_row_to_model(updated_data)
            if updated_proc:
                logger.info(f"Processo Licitatório ID {id} atualizado de '{proc_antigo.numero}' para '{updated_proc.numero}'.")
            return updated_proc

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            if isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao atualizar processo licitatório ID {id} para '{proc_req.numero}'. Número duplicado?")
            else:
                 logger.exception(f"Erro inesperado ao atualizar processo licitatório ID {id} (Req: {proc_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        proc_para_deletar = self.get_by_id(id)
        if not proc_para_deletar:
             logger.warning(f"Tentativa de deletar processo licitatório ID {id} falhou (não encontrado).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM processoslicitatorios WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"Processo Licitatório ID {id} ('{proc_para_deletar.numero}') deletado.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error:
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar processo licitatório ID {id} ('{proc_para_deletar.numero}'). Vinculado a Contratos.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar processo licitatório ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()

    def get_by_numero(self, numero: str) -> ProcessoLicitatorio | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM processoslicitatorios WHERE numero = %s"
            cursor.execute(sql, (numero,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar processo licitatório por numero ('{numero}'): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_or_create(self, numero: str) -> ProcessoLicitatorio:
        try:
            proc = self.get_by_numero(numero) 
            if proc:
                return proc
        except Exception:
             logger.exception(f"Erro ao buscar processo licitatório '{numero}' em get_or_create. Tentando criar...")

        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO processoslicitatorios (numero) VALUES (%s) RETURNING *"
            cursor.execute(sql, (numero,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            new_proc = self._map_row_to_model(new_data)
            if not new_proc:
                 log_message = f"Falha ao mapear processo licitatório '{numero}' recém-criado em get_or_create."
                 logger.error(log_message)
                 raise Exception(log_message)

            logger.info(f"Processo Licitatório '{numero}' não encontrado/erro na busca, criado novo com ID {new_proc.id}.")
            return new_proc

        except psycopg2.IntegrityError:
            logging.warning(f"IntegrityError ao criar processo licitatório '{numero}' em get_or_create. Já existe. Buscando novamente.")
            self.db_conn.rollback()
            if cursor and not cursor.closed: cursor.close()

            proc_existente = self.get_by_numero(numero) 
            if proc_existente:
                return proc_existente
            else:
                log_message = f"Erro INESPERADO ao buscar processo licitatório '{numero}' após conflito de inserção."
                logger.exception(log_message)
                raise Exception(log_message)

        except (Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             logger.exception(f"Erro inesperado na criação do get_or_create para processo licitatório '{numero}': {error}")
             raise
        finally:
            if cursor and not cursor.closed:
                cursor.close()