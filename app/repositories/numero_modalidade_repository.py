import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
import logging
from app.models.numero_modalidade_model import NumeroModalidade 
from app.schemas.numero_modalidade_schema import NumeroModalidadeRequest 

logger = logging.getLogger(__name__)

class NumeroModalidadeRepository: 
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    def _map_row_to_model(self, row: DictCursor | None) -> NumeroModalidade | None:
        if not row:
            return None
        try:
            return NumeroModalidade(id=row['id'], numero_ano=row['numero_ano'])
        except KeyError as e:
            logger.error(f"Erro de mapeamento NumeroModalidade: Coluna '{e}' não encontrada.")
            return None

    def create(self, num_mod_req: NumeroModalidadeRequest) -> NumeroModalidade:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO numeromodalidade (numero_ano) VALUES (%s) RETURNING *"
            cursor.execute(sql, (num_mod_req.numero_ano,))
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_num_mod = self._map_row_to_model(new_data)
            if not new_num_mod:
                logger.error("Falha ao mapear dados do numero_modalidade recém-criado.")
                raise Exception("Falha ao mapear dados do numero_modalidade recém-criado.")

            logger.info(f"NumeroModalidade criado com ID {new_num_mod.id}: '{new_num_mod.numero_ano}'")
            return new_num_mod

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao criar numero_modalidade (Req: {num_mod_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_all(self) -> list[NumeroModalidade]:
        cursor = None
        num_mods = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM numeromodalidade ORDER BY numero_ano"
            cursor.execute(sql)
            all_data = cursor.fetchall()
            num_mods = [self._map_row_to_model(row) for row in all_data if row]
            num_mods = [nm for nm in num_mods if nm is not None]
            return num_mods
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar numero_modalidade: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> NumeroModalidade | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM numeromodalidade WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar numero_modalidade por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def update(self, id: int, num_mod_req: NumeroModalidadeRequest) -> NumeroModalidade | None:
        cursor = None
        num_mod_antigo = self.get_by_id(id)
        if not num_mod_antigo:
             logger.warning(f"Tentativa de atualizar numero_modalidade ID {id} falhou (não encontrado).")
             return None

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE numeromodalidade SET numero_ano = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (num_mod_req.numero_ano, id))
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_num_mod = self._map_row_to_model(updated_data)
            if updated_num_mod:
                logger.info(f"NumeroModalidade ID {id} atualizado de '{num_mod_antigo.numero_ano}' para '{updated_num_mod.numero_ano}'.")
            return updated_num_mod

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            if isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao atualizar numero_modalidade ID {id} para '{num_mod_req.numero_ano}'. Valor duplicado?")
            else:
                 logger.exception(f"Erro inesperado ao atualizar numero_modalidade ID {id} (Req: {num_mod_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        num_mod_para_deletar = self.get_by_id(id)
        if not num_mod_para_deletar:
             logger.warning(f"Tentativa de deletar numero_modalidade ID {id} falhou (não encontrado).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM numeromodalidade WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"NumeroModalidade ID {id} ('{num_mod_para_deletar.numero_ano}') deletado.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error:
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar numero_modalidade ID {id} ('{num_mod_para_deletar.numero_ano}'). Vinculado a Contratos.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar numero_modalidade ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()

    def get_by_numero_ano(self, numero_ano: str) -> NumeroModalidade | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM numeromodalidade WHERE numero_ano = %s"
            cursor.execute(sql, (numero_ano,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar numero_modalidade por numero_ano ('{numero_ano}'): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_or_create(self, numero_ano: str) -> NumeroModalidade:
        try:
            num_mod = self.get_by_numero_ano(numero_ano) 
            if num_mod:
                return num_mod
        except Exception:
             logger.exception(f"Erro ao buscar numero_modalidade '{numero_ano}' em get_or_create. Tentando criar...")

        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO numeromodalidade (numero_ano) VALUES (%s) RETURNING *"
            cursor.execute(sql, (numero_ano,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            new_num_mod = self._map_row_to_model(new_data)
            if not new_num_mod:
                 log_message = f"Falha ao mapear numero_modalidade '{numero_ano}' recém-criado em get_or_create."
                 logger.error(log_message)
                 raise Exception(log_message)

            logger.info(f"NumeroModalidade '{numero_ano}' não encontrado/erro na busca, criado novo com ID {new_num_mod.id}.")
            return new_num_mod

        except psycopg2.IntegrityError:
            logging.warning(f"IntegrityError ao criar numero_modalidade '{numero_ano}' em get_or_create. Já existe. Buscando novamente.")
            self.db_conn.rollback()
            if cursor and not cursor.closed: cursor.close()

            num_mod_existente = self.get_by_numero_ano(numero_ano)
            if num_mod_existente:
                return num_mod_existente
            else:
                log_message = f"Erro INESPERADO ao buscar numero_modalidade '{numero_ano}' após conflito de inserção."
                logger.exception(log_message)
                raise Exception(log_message)

        except (Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             logger.exception(f"Erro inesperado na criação do get_or_create para numero_modalidade '{numero_ano}': {error}")
             raise
        finally:
            if cursor and not cursor.closed:
                cursor.close()