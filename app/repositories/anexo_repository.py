import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from datetime import date
import logging
from app.models.anexo_model import Anexo
from app.schemas.anexo_schema import AnexoCreate # Usamos o schema Create aqui
from .tipo_documento_repository import TipoDocumentoRepository

logger = logging.getLogger(__name__)

class AnexoRepository: 
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn
        self.tipodocumento_repo = TipoDocumentoRepository(db_conn)

    def _map_row_to_model(self, row: DictCursor | None) -> Anexo | None:
        if not row:
            return None
        try:
            return Anexo(
                id=row['id'],
                id_entidade=row['id_entidade'],
                nome_original=row.get('nome_original'), 
                nome_seguro=row['nome_seguro'],
                data_upload=row['data_upload'],
                tipo_documento=row.get('tipo_documento'), 
                tipo_entidade=row['tipo_entidade']
            )
        except KeyError as e:
            logger.error(f"Erro de mapeamento Anexo: Coluna '{e}' não encontrada.")
            return None

    def create(self, anexo_create_data: AnexoCreate) -> Anexo:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = """
                INSERT INTO anexos (id_entidade, tipo_entidade, tipo_documento,
                                    nome_original, nome_seguro, data_upload)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
            """
            params = (
                anexo_create_data.id_entidade,
                anexo_create_data.tipo_entidade,
                anexo_create_data.tipo_documento, 
                anexo_create_data.nome_original,
                anexo_create_data.nome_seguro,
                anexo_create_data.data_upload
            )
            cursor.execute(sql, params)
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_anexo = self._map_row_to_model(new_data)
            if not new_anexo:
                logger.error("Falha ao mapear dados do anexo recém-criado.")
                raise Exception("Falha ao mapear dados do anexo recém-criado.")

            logger.info(f"Registro de Anexo criado com ID {new_anexo.id} para {new_anexo.tipo_entidade} ID {new_anexo.id_entidade} ('{new_anexo.nome_original}')")
            return new_anexo

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao criar registro de anexo (Data: {anexo_create_data}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> Anexo | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM anexos WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar anexo por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_all(self) -> list[Anexo]:
        cursor = None
        anexos = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM anexos ORDER BY data_upload DESC, id DESC" 
            cursor.execute(sql)
            all_data = cursor.fetchall()
            anexos = [self._map_row_to_model(row) for row in all_data if row]
            anexos = [anexo for anexo in anexos if anexo is not None]
            return anexos
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar anexos: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def get_by_entidade(self, id_entidade: int, tipo_entidade: str) -> list[Anexo]:
        cursor = None
        anexos = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM anexos WHERE id_entidade = %s AND tipo_entidade = %s ORDER BY data_upload DESC, id DESC"
            cursor.execute(sql, (id_entidade, tipo_entidade))
            all_data = cursor.fetchall()
            anexos = [self._map_row_to_model(row) for row in all_data if row]
            anexos = [anexo for anexo in anexos if anexo is not None]
            return anexos
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar anexos para {tipo_entidade} ID {id_entidade}: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> tuple[bool, Anexo | None]:
        """Deleta o registro de metadados de um anexo. Retorna sucesso e o objeto deletado."""
        cursor = None
        anexo_para_deletar = self.get_by_id(id)
        if not anexo_para_deletar:
             logger.warning(f"Tentativa de deletar anexo ID {id} falhou (não encontrado).")
             return False, None

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM anexos WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"Registro de Anexo ID {id} ('{anexo_para_deletar.nome_original}') deletado.")
                return True, anexo_para_deletar
            else:
                 logger.error(f"Falha ao deletar anexo ID {id} (existente). Nenhuma linha afetada.")
                 return False, anexo_para_deletar

        except psycopg2.IntegrityError as fk_error: 
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao tentar deletar anexo ID {id}.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar anexo ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()