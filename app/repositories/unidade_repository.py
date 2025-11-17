import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
import logging
from app.models.unidade_model import Unidade 
from app.schemas.unidade_schema import UnidadeRequest 

logger = logging.getLogger(__name__)

class UnidadeRepository: 
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    def _map_row_to_model(self, row: DictCursor | None) -> Unidade | None:
        if not row:
            return None
        try:
            return Unidade(id=row['id'], nome=row['nome'])
        except KeyError as e:
            logger.error(f"Erro de mapeamento Unidade: Coluna '{e}' não encontrada.")
            return None

    def create(self, unidade_req: UnidadeRequest) -> Unidade:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO unidadesrequisitantes (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (unidade_req.nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_unidade = self._map_row_to_model(new_data)
            if not new_unidade:
                logger.error("Falha ao mapear dados da unidade recém-criada.")
                raise Exception("Falha ao mapear dados da unidade recém-criada.")

            logger.info(f"Unidade criada com ID {new_unidade.id}: '{new_unidade.nome}'")
            return new_unidade

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao criar unidade (Req: {unidade_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_all(self) -> list[Unidade]:
        cursor = None
        unidades = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM unidadesrequisitantes ORDER BY nome"
            cursor.execute(sql)
            all_data = cursor.fetchall()
            unidades = [self._map_row_to_model(row) for row in all_data if row]
            unidades = [u for u in unidades if u is not None]
            return unidades
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar unidades: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> Unidade | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM unidadesrequisitantes WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar unidade por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def update(self, id: int, unidade_req: UnidadeRequest) -> Unidade | None:
        cursor = None
        unidade_antiga = self.get_by_id(id)
        if not unidade_antiga:
             logger.warning(f"Tentativa de atualizar unidade ID {id} falhou (não encontrada).")
             return None

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE unidadesrequisitantes SET nome = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (unidade_req.nome, id))
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_unidade = self._map_row_to_model(updated_data)
            if updated_unidade:
                logger.info(f"Unidade ID {id} atualizada de '{unidade_antiga.nome}' para '{updated_unidade.nome}'.")
            return updated_unidade

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            if isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao atualizar unidade ID {id} para '{unidade_req.nome}'. Nome duplicado?")
            else:
                 logger.exception(f"Erro inesperado ao atualizar unidade ID {id} (Req: {unidade_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        unidade_para_deletar = self.get_by_id(id)
        if not unidade_para_deletar:
             logger.warning(f"Tentativa de deletar unidade ID {id} falhou (não encontrada).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM unidadesrequisitantes WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"Unidade ID {id} ('{unidade_para_deletar.nome}') deletada.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error:
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar unidade ID {id} ('{unidade_para_deletar.nome}'). Vinculada a AOCS/CI.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar unidade ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()

    def get_by_nome(self, nome: str) -> Unidade | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM unidadesrequisitantes WHERE nome = %s"
            cursor.execute(sql, (nome,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar unidade por nome ('{nome}'): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_or_create(self, nome: str) -> Unidade:
        try:
            unidade = self.get_by_nome(nome)
            if unidade:
                return unidade
        except Exception:
             logger.exception(f"Erro ao buscar unidade '{nome}' em get_or_create. Tentando criar...")

        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO unidadesrequisitantes (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            new_unidade = self._map_row_to_model(new_data)
            if not new_unidade:
                 log_message = f"Falha ao mapear unidade '{nome}' recém-criada em get_or_create."
                 logger.error(log_message)
                 raise Exception(log_message)

            logger.info(f"Unidade '{nome}' não encontrada/erro na busca, criada nova com ID {new_unidade.id}.")
            return new_unidade

        except psycopg2.IntegrityError:
            logging.warning(f"IntegrityError ao criar unidade '{nome}' em get_or_create. Já existe. Buscando novamente.")
            self.db_conn.rollback()
            if cursor and not cursor.closed: cursor.close()

            unidade_existente = self.get_by_nome(nome)
            if unidade_existente:
                return unidade_existente
            else:
                log_message = f"Erro INESPERADO ao buscar unidade '{nome}' após conflito de inserção."
                logger.exception(log_message)
                raise Exception(log_message)

        except (Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             logger.exception(f"Erro inesperado na criação do get_or_create para unidade '{nome}': {error}")
             raise
        finally:
            if cursor and not cursor.closed:
                cursor.close()