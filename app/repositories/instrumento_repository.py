import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from typing import List
import logging
from app.models.instrumento_model import Instrumento
from app.schemas.instrumento_schema import InstrumentoRequest

logger = logging.getLogger(__name__)

class InstrumentoRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    def _map_row_to_model(self, row: DictCursor | None) -> Instrumento | None:
        if not row:
            return None
        try:
            return Instrumento(id=row['id'], nome=row['nome'])
        except KeyError as e:
            logger.error(f"Erro de mapeamento Instrumento: Coluna '{e}' não encontrada.")
            return None

    def create(self, instrumento_req: InstrumentoRequest) -> Instrumento:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO instrumentocontratual (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (instrumento_req.nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_instrumento = self._map_row_to_model(new_data)
            if not new_instrumento:
                logger.error("Falha ao mapear dados do instrumento recém-criado.")
                raise Exception("Falha ao mapear dados do instrumento recém-criado.")

            logger.info(f"Instrumento criado com ID {new_instrumento.id}: '{new_instrumento.nome}'")
            return new_instrumento

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao criar instrumento (Req: {instrumento_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_all(self) -> List[Instrumento]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM instrumentocontratual ORDER BY nome" 
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            return [self._map_row_to_model(row) for row in rows if row]
        
        except (Exception, psycopg2.DatabaseError) as error:
            logger.exception(f"Erro ao buscar todos os Instrumentos: {error}")
            raise
        finally:
            if cursor:
                cursor.close()

    def get_by_id(self, id: int) -> Instrumento | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM instrumentocontratual WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar instrumento por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def update(self, id: int, instrumento_req: InstrumentoRequest) -> Instrumento | None:
        cursor = None
        instrumento_antigo = self.get_by_id(id)
        if not instrumento_antigo:
             logger.warning(f"Tentativa de atualizar instrumento ID {id} falhou (não encontrado).")
             return None

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE instrumentocontratual SET nome = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (instrumento_req.nome, id))
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_instrumento = self._map_row_to_model(updated_data)
            if updated_instrumento:
                logger.info(f"Instrumento ID {id} atualizado de '{instrumento_antigo.nome}' para '{updated_instrumento.nome}'.")
            return updated_instrumento

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            if isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao atualizar instrumento ID {id} para '{instrumento_req.nome}'. Nome duplicado?")
            else:
                 logger.exception(f"Erro inesperado ao atualizar instrumento ID {id} (Req: {instrumento_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        instrumento_para_deletar = self.get_by_id(id)
        if not instrumento_para_deletar:
             logger.warning(f"Tentativa de deletar instrumento ID {id} falhou (não encontrado).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM instrumentocontratual WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"Instrumento ID {id} ('{instrumento_para_deletar.nome}') deletado.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error:
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar instrumento ID {id} ('{instrumento_para_deletar.nome}'). Vinculado a Contratos.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar instrumento ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()

    def get_by_nome(self, nome: str) -> Instrumento | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM instrumentocontratual WHERE nome = %s"
            cursor.execute(sql, (nome,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar instrumento por nome ('{nome}'): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_or_create(self, nome: str) -> Instrumento:
        try:
            instrumento = self.get_by_nome(nome)
            if instrumento:
                return instrumento
        except Exception:
             logger.exception(f"Erro ao buscar instrumento '{nome}' em get_or_create. Tentando criar...")

        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO instrumentocontratual (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            new_instrumento = self._map_row_to_model(new_data)
            if not new_instrumento:
                 log_message = f"Falha ao mapear instrumento '{nome}' recém-criado em get_or_create."
                 logger.error(log_message)
                 raise Exception(log_message)

            logger.info(f"Instrumento '{nome}' não encontrado/erro na busca, criado novo com ID {new_instrumento.id}.")
            return new_instrumento

        except psycopg2.IntegrityError:
            logging.warning(f"IntegrityError ao criar instrumento '{nome}' em get_or_create. Já existe. Buscando novamente.")
            self.db_conn.rollback()
            if cursor and not cursor.closed: cursor.close()

            instrumento_existente = self.get_by_nome(nome)
            if instrumento_existente:
                return instrumento_existente
            else:
                log_message = f"Erro INESPERADO ao buscar instrumento '{nome}' após conflito de inserção."
                logger.exception(log_message)
                raise Exception(log_message)

        except (Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             logger.exception(f"Erro inesperado na criação do get_or_create para instrumento '{nome}': {error}")
             raise
        finally:
            if cursor and not cursor.closed:
                cursor.close()