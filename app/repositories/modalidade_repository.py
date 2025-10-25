import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
import logging
from app.models.modalidade_model import Modalidade 
from app.schemas.modalidade_schema import ModalidadeRequest 

logger = logging.getLogger(__name__)

class ModalidadeRepository: 
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    def _map_row_to_model(self, row: DictCursor | None) -> Modalidade | None:
        if not row:
            return None
        try:
            return Modalidade(id=row['id'], nome=row['nome'])
        except KeyError as e:
            logger.error(f"Erro de mapeamento Modalidade: Coluna '{e}' não encontrada.")
            return None

    def create(self, modalidade_req: ModalidadeRequest) -> Modalidade:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO modalidade (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (modalidade_req.nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_modalidade = self._map_row_to_model(new_data)
            if not new_modalidade:
                logger.error("Falha ao mapear dados da modalidade recém-criada.")
                raise Exception("Falha ao mapear dados da modalidade recém-criada.")

            logger.info(f"Modalidade criada com ID {new_modalidade.id}: '{new_modalidade.nome}'")
            return new_modalidade

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao criar modalidade (Req: {modalidade_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_all(self) -> list[Modalidade]:
        cursor = None
        modalidades = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM modalidade ORDER BY nome"
            cursor.execute(sql)
            all_data = cursor.fetchall()
            modalidades = [self._map_row_to_model(row) for row in all_data if row]
            modalidades = [mod for mod in modalidades if mod is not None]
            return modalidades
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar modalidades: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> Modalidade | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM modalidade WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar modalidade por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def update(self, id: int, modalidade_req: ModalidadeRequest) -> Modalidade | None:
        cursor = None
        modalidade_antiga = self.get_by_id(id)
        if not modalidade_antiga:
             logger.warning(f"Tentativa de atualizar modalidade ID {id} falhou (não encontrada).")
             return None

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE modalidade SET nome = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (modalidade_req.nome, id))
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_modalidade = self._map_row_to_model(updated_data)
            if updated_modalidade:
                logger.info(f"Modalidade ID {id} atualizada de '{modalidade_antiga.nome}' para '{updated_modalidade.nome}'.")
            return updated_modalidade

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            if isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao atualizar modalidade ID {id} para '{modalidade_req.nome}'. Nome duplicado?")
            else:
                 logger.exception(f"Erro inesperado ao atualizar modalidade ID {id} (Req: {modalidade_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        modalidade_para_deletar = self.get_by_id(id)
        if not modalidade_para_deletar:
             logger.warning(f"Tentativa de deletar modalidade ID {id} falhou (não encontrada).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM modalidade WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"Modalidade ID {id} ('{modalidade_para_deletar.nome}') deletada.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error:
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar modalidade ID {id} ('{modalidade_para_deletar.nome}'). Vinculada a Contratos.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar modalidade ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()

    def get_by_nome(self, nome: str) -> Modalidade | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM modalidade WHERE nome = %s"
            cursor.execute(sql, (nome,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar modalidade por nome ('{nome}'): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_or_create(self, nome: str) -> Modalidade:
        try:
            modalidade = self.get_by_nome(nome)
            if modalidade:
                return modalidade
        except Exception:
             logger.exception(f"Erro ao buscar modalidade '{nome}' em get_or_create. Tentando criar...")

        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO modalidade (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            new_modalidade = self._map_row_to_model(new_data)
            if not new_modalidade:
                 log_message = f"Falha ao mapear modalidade '{nome}' recém-criada em get_or_create."
                 logger.error(log_message)
                 raise Exception(log_message)

            logger.info(f"Modalidade '{nome}' não encontrada/erro na busca, criada nova com ID {new_modalidade.id}.")
            return new_modalidade

        except psycopg2.IntegrityError:
            logging.warning(f"IntegrityError ao criar modalidade '{nome}' em get_or_create. Já existe. Buscando novamente.")
            self.db_conn.rollback()
            if cursor and not cursor.closed: cursor.close()

            modalidade_existente = self.get_by_nome(nome)
            if modalidade_existente:
                return modalidade_existente
            else:
                log_message = f"Erro INESPERADO ao buscar modalidade '{nome}' após conflito de inserção."
                logger.exception(log_message)
                raise Exception(log_message)

        except (Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             logger.exception(f"Erro inesperado na criação do get_or_create para modalidade '{nome}': {error}")
             raise
        finally:
            if cursor and not cursor.closed:
                cursor.close()