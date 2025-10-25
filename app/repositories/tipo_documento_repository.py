import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
import logging
from app.models.tipo_documento_model import TipoDocumento
from app.schemas.tipo_documento_schema import TipoDocumentoRequest

logger = logging.getLogger(__name__)

class TipoDocumentoRepository: 
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    def _map_row_to_model(self, row: DictCursor | None) -> TipoDocumento | None:
        if not row:
            return None
        try:
            return TipoDocumento(id=row['id'], nome=row['nome'])
        except KeyError as e:
            logger.error(f"Erro de mapeamento TipoDocumento: Coluna '{e}' não encontrada.")
            return None

    def create(self, tipo_doc_req: TipoDocumentoRequest) -> TipoDocumento:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO tipos_documento (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (tipo_doc_req.nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_tipo_doc = self._map_row_to_model(new_data)
            if not new_tipo_doc:
                logger.error("Falha ao mapear dados do tipo de documento recém-criado.")
                raise Exception("Falha ao mapear dados do tipo de documento recém-criado.")

            logger.info(f"TipoDocumento criado com ID {new_tipo_doc.id}: '{new_tipo_doc.nome}'")
            return new_tipo_doc

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao criar tipo de documento (Req: {tipo_doc_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_all(self) -> list[TipoDocumento]:
        cursor = None
        tipos_doc = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM tipos_documento ORDER BY nome"
            cursor.execute(sql)
            all_data = cursor.fetchall()
            tipos_doc = [self._map_row_to_model(row) for row in all_data if row]
            tipos_doc = [td for td in tipos_doc if td is not None]
            return tipos_doc
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar tipos de documento: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> TipoDocumento | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM tipos_documento WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar tipo de documento por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def update(self, id: int, tipo_doc_req: TipoDocumentoRequest) -> TipoDocumento | None:
        cursor = None
        tipo_doc_antigo = self.get_by_id(id)
        if not tipo_doc_antigo:
             logger.warning(f"Tentativa de atualizar tipo de documento ID {id} falhou (não encontrado).")
             return None

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE tipos_documento SET nome = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (tipo_doc_req.nome, id))
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_tipo_doc = self._map_row_to_model(updated_data)
            if updated_tipo_doc:
                logger.info(f"TipoDocumento ID {id} atualizado de '{tipo_doc_antigo.nome}' para '{updated_tipo_doc.nome}'.")
            return updated_tipo_doc

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            if isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao atualizar tipo de documento ID {id} para '{tipo_doc_req.nome}'. Nome duplicado?")
            else:
                 logger.exception(f"Erro inesperado ao atualizar tipo de documento ID {id} (Req: {tipo_doc_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        tipo_doc_para_deletar = self.get_by_id(id)
        if not tipo_doc_para_deletar:
             logger.warning(f"Tentativa de deletar tipo de documento ID {id} falhou (não encontrado).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM tipos_documento WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"TipoDocumento ID {id} ('{tipo_doc_para_deletar.nome}') deletado.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error:
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar tipo de documento ID {id} ('{tipo_doc_para_deletar.nome}'). Vinculado a Anexos.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar tipo de documento ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()

    def get_by_nome(self, nome: str) -> TipoDocumento | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM tipos_documento WHERE nome = %s"
            cursor.execute(sql, (nome,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar tipo de documento por nome ('{nome}'): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_or_create(self, nome: str) -> TipoDocumento:
        try:
            tipo_doc = self.get_by_nome(nome)
            if tipo_doc:
                return tipo_doc
        except Exception:
             logger.exception(f"Erro ao buscar tipo de documento '{nome}' em get_or_create. Tentando criar...")

        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO tipos_documento (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            new_tipo_doc = self._map_row_to_model(new_data)
            if not new_tipo_doc:
                 log_message = f"Falha ao mapear tipo de documento '{nome}' recém-criado em get_or_create."
                 logger.error(log_message)
                 raise Exception(log_message)

            logger.info(f"TipoDocumento '{nome}' não encontrado/erro na busca, criado novo com ID {new_tipo_doc.id}.")
            return new_tipo_doc

        except psycopg2.IntegrityError:
            logging.warning(f"IntegrityError ao criar tipo de documento '{nome}' em get_or_create. Já existe. Buscando novamente.")
            self.db_conn.rollback()
            if cursor and not cursor.closed: cursor.close()

            tipo_doc_existente = self.get_by_nome(nome)
            if tipo_doc_existente:
                return tipo_doc_existente
            else:
                log_message = f"Erro INESPERADO ao buscar tipo de documento '{nome}' após conflito de inserção."
                logger.exception(log_message)
                raise Exception(log_message)

        except (Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             logger.exception(f"Erro inesperado na criação do get_or_create para tipo de documento '{nome}': {error}")
             raise
        finally:
            if cursor and not cursor.closed:
                cursor.close()