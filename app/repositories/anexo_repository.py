import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from datetime import date
import logging
from app.models.anexo_model import Anexo
from app.schemas.anexo_schema import AnexoCreate 
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
                nome_original=row.get('nome_original'), 
                nome_seguro=row['nome_seguro'],
                data_upload=row['data_upload'],
                tipo_documento=row.get('tipo_documento'), 
                tipo_entidade=row['tipo_entidade'],
                id_contrato=row.get('id_contrato'),
                id_aocs=row.get('id_aocs')
            )
        except (KeyError, TypeError) as e:
            logger.error(f"Erro de mapeamento Anexo: {e}. Linha do DB: {row}")
            return None

    def create(self, anexo_create_data: AnexoCreate) -> Anexo:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            cols = ["tipo_entidade", "nome_original", "nome_seguro", 
                    "data_upload", "tipo_documento"]
            
            params = [anexo_create_data.tipo_entidade, anexo_create_data.nome_original, 
                      anexo_create_data.nome_seguro, anexo_create_data.data_upload, 
                      anexo_create_data.tipo_documento]

            if anexo_create_data.tipo_entidade == 'contrato':
                cols.append("id_contrato")
                params.append(anexo_create_data.id_entidade)
            elif anexo_create_data.tipo_entidade == 'aocs':
                cols.append("id_aocs")
                params.append(anexo_create_data.id_entidade)
            else:
                logger.warning(f"Tentativa de criar anexo com tipo_entidade desconhecido: {anexo_create_data.tipo_entidade}")

            sql_cols = ", ".join(cols)
            sql_placeholders = ", ".join(["%s"] * len(params))
            
            sql = f"INSERT INTO anexos ({sql_cols}) VALUES ({sql_placeholders}) RETURNING *"

            cursor.execute(sql, tuple(params))
            
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_anexo = self._map_row_to_model(new_data)
            if not new_anexo:
                logger.error("Falha ao mapear dados do anexo recém-criado.")
                raise Exception("Falha ao mapear dados do anexo recém-criado.")
            
            logger.info(f"Anexo ID {new_anexo.id} ('{new_anexo.nome_original}') criado e vinculado a {new_anexo.tipo_entidade}.")
            return new_anexo

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao criar registro de anexo (Data: {anexo_create_data}): {error}")
            raise
        finally:
            if cursor:
                cursor.close()

    def get_by_entidade(self, id_entidade: int, tipo_entidade: str) -> list[Anexo]:
        cursor = None
        
        # Define qual coluna de ID usar
        if tipo_entidade == 'contrato':
            fk_column = "id_contrato"
        elif tipo_entidade == 'aocs':
            fk_column = "id_aocs"
        else:
            logger.warning(f"get_by_entidade chamado com tipo desconhecido: {tipo_entidade}")
            return [] 

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            # [CORREÇÃO] Simplificamos a query para garantir compatibilidade
            # Se a coluna tipo_entidade for o problema, podemos removê-la daqui temporariamente
            # Mas como ela existe no dump, vamos manter, mas garantindo a sintaxe.
            
            sql = f"""
                SELECT * FROM anexos 
                WHERE {fk_column} = %s 
                AND tipo_entidade = %s 
                ORDER BY data_upload DESC
            """
            
            params = (id_entidade, tipo_entidade)
            
            logger.debug(f"SQL Anexos: {sql} | Params: {params}")

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            return [anexo for anexo in (self._map_row_to_model(row) for row in rows) if anexo]

        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro ao buscar anexos ({tipo_entidade}={id_entidade}): {error}")
             return []
        finally:
            if cursor:
                cursor.close()

    def get_by_id(self, id: int) -> Anexo | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM anexos WHERE id = %s"
            cursor.execute(sql, (id,))
            row = cursor.fetchone()
            return self._map_row_to_model(row)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro ao buscar anexo ID {id}: {error}")
             return None
        finally:
            if cursor:
                cursor.close()

    def delete(self, id: int) -> tuple[bool, Anexo | None]:
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
             raise
        finally:
            if cursor:
                cursor.close()