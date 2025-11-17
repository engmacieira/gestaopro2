import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
import logging
from app.models.agente_model import Agente 
from app.schemas.agente_schema import AgenteRequest 

logger = logging.getLogger(__name__)

class AgenteRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn

    def _map_row_to_model(self, row: DictCursor | None) -> Agente | None:
        if not row:
            return None
        try:
            return Agente(id=row['id'], nome=row['nome'])
        except KeyError as e:
            logger.error(f"Erro de mapeamento Agente: Coluna '{e}' não encontrada.")
            return None 

    def create(self, agente_req: AgenteRequest) -> Agente:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO agentesresponsaveis (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (agente_req.nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_agente = self._map_row_to_model(new_data)
            if not new_agente:
                logger.error("Falha ao mapear dados do agente recém-criado.")
                raise Exception("Falha ao mapear dados do agente recém-criado.")

            logger.info(f"Agente criado com ID {new_agente.id}: '{new_agente.nome}'")
            return new_agente

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao criar agente (Req: {agente_req}): {error}")
            raise 
        finally:
            if cursor: cursor.close()

    def get_all(self) -> list[Agente]:
        """Lista todos os Agentes Responsáveis."""
        cursor = None
        agentes = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM agentesresponsaveis ORDER BY nome"
            cursor.execute(sql)
            all_data = cursor.fetchall()
            agentes = [self._map_row_to_model(row) for row in all_data if row]
            agentes = [agente for agente in agentes if agente is not None]
            return agentes
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar agentes: {error}")
             return [] 
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> Agente | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM agentesresponsaveis WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data) 
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar agente por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def update(self, id: int, agente_req: AgenteRequest) -> Agente | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE agentesresponsaveis SET nome = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (agente_req.nome, id))
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_agente = self._map_row_to_model(updated_data)
            if updated_agente:
                logger.info(f"Agente ID {id} atualizado para nome '{updated_agente.nome}'")
            else:
                logger.warning(f"Tentativa de atualizar agente ID {id} falhou (não encontrado).")
            return updated_agente

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao atualizar agente ID {id} (Req: {agente_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        agente_para_deletar = self.get_by_id(id) 
        if not agente_para_deletar:
             logger.warning(f"Tentativa de deletar agente ID {id} falhou (não encontrado).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM agentesresponsaveis WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"Agente ID {id} ('{agente_para_deletar.nome}') deletado.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error: 
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar agente ID {id} ('{agente_para_deletar.nome}'). Vinculado a AOCS.")
             raise fk_error 
        except (Exception, psycopg2.DatabaseError) as error: 
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar agente ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()

    def get_by_nome(self, nome: str) -> Agente | None:
        """Busca um Agente Responsável pelo nome exato."""
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM agentesresponsaveis WHERE nome = %s"
            cursor.execute(sql, (nome,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar agente por nome ('{nome}'): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_or_create(self, nome: str) -> Agente:
        """Busca um Agente pelo nome ou cria um novo se não existir."""
        try:
            agente = self.get_by_nome(nome)
            if agente:
                return agente
        except Exception:
             logger.exception(f"Erro ao buscar agente '{nome}' em get_or_create. Tentando criar...")

        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "INSERT INTO agentesresponsaveis (nome) VALUES (%s) RETURNING *"
            cursor.execute(sql, (nome,))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            new_agente = self._map_row_to_model(new_data)
            if not new_agente:
                 log_message = f"Falha ao mapear agente '{nome}' recém-criado em get_or_create."
                 logger.error(log_message)
                 raise Exception(log_message)

            logger.info(f"Agente '{nome}' não encontrado/erro na busca, criado novo com ID {new_agente.id}.")
            return new_agente

        except psycopg2.IntegrityError:
            logging.warning(f"IntegrityError ao criar agente '{nome}' em get_or_create. Já existe. Buscando novamente.")
            self.db_conn.rollback()
            if cursor and not cursor.closed: cursor.close()

            agente_existente = self.get_by_nome(nome)
            if agente_existente:
                return agente_existente
            else:
                log_message = f"Erro INESPERADO ao buscar agente '{nome}' após conflito de inserção em get_or_create."
                logger.exception(log_message)
                raise Exception(log_message)

        except (Exception, psycopg2.DatabaseError) as error: 
             if self.db_conn: self.db_conn.rollback()
             logger.exception(f"Erro inesperado na criação do get_or_create para agente '{nome}': {error}")
             raise
        finally:
            if cursor and not cursor.closed:
                cursor.close()