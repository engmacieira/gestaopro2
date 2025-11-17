import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from datetime import date
import logging
from app.models.aocs_model import Aocs
from app.schemas.aocs_schema import AocsCreateRequest, AocsUpdateRequest 
from .unidade_repository import UnidadeRepository
from .local_repository import LocalRepository
from .agente_repository import AgenteRepository
from .dotacao_repository import DotacaoRepository

logger = logging.getLogger(__name__)

class AocsRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn
        self.unidade_repo = UnidadeRepository(db_conn)
        self.local_repo = LocalRepository(db_conn)
        self.agente_repo = AgenteRepository(db_conn)
        self.dotacao_repo = DotacaoRepository(db_conn)

    def _map_row_to_model(self, row: DictCursor | None) -> Aocs | None:
        if not row:
            return None
        try:
            return Aocs(
                id=row['id'],
                numero_aocs=row['numero_aocs'],
                data_criacao=row['data_criacao'],
                justificativa=row['justificativa'],
                id_unidade_requisitante=row['id_unidade_requisitante'],
                id_local_entrega=row['id_local_entrega'],
                id_agente_responsavel=row['id_agente_responsavel'],
                id_dotacao=row['id_dotacao'],
                numero_pedido=row.get('numero_pedido'),
                empenho=row.get('empenho'),
            )
        except KeyError as e:
            logger.error(f"Erro de mapeamento AOCS: Coluna '{e}' não encontrada.")
            return None

    def create(self, aocs_req: AocsCreateRequest) -> Aocs:
        cursor = None
        try:
            uni = self.unidade_repo.get_or_create(aocs_req.unidade_requisitante_nome)
            
            loc = self.local_repo.get_or_create(aocs_req.local_entrega_descricao) 
            
            age = self.agente_repo.get_or_create(aocs_req.agente_responsavel_nome)
            
            dot = self.dotacao_repo.get_or_create(aocs_req.dotacao_info_orcamentaria) 
            
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = """
                INSERT INTO aocs (numero_aocs, justificativa, data_criacao,
                                id_unidade_requisitante, id_local_entrega,
                                id_agente_responsavel, id_dotacao, numero_pedido, empenho)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """ 
            params = (
                aocs_req.numero_aocs, aocs_req.justificativa, aocs_req.data_criacao,
                uni.id, loc.id, age.id, dot.id,
                aocs_req.numero_pedido, aocs_req.empenho
            )
            cursor.execute(sql, params)
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_aocs = self._map_row_to_model(new_data)
            if not new_aocs:
                logger.error("Falha ao mapear dados da AOCS recém-criada.")
                raise Exception("Falha ao mapear dados da AOCS recém-criada.")

            logger.info(f"AOCS criada com ID {new_aocs.id} ('{new_aocs.numero_aocs}')")
            return new_aocs

        except (ValueError, Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            if isinstance(error, ValueError):
                 logger.warning(f"Erro ao resolver FKs durante criação da AOCS (Req: {aocs_req}): {error}")
            else:
                 logger.exception(f"Erro inesperado ao criar AOCS (Req: {aocs_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> Aocs | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM aocs WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar AOCS por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_by_numero_aocs(self, numero_aocs: str) -> Aocs | None: 
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM aocs WHERE numero_aocs = %s"
            cursor.execute(sql, (numero_aocs,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar AOCS por Numero ('{numero_aocs}'): {error}")
             return None
        finally:
            if cursor: cursor.close()


    def get_all(self) -> list[Aocs]:
        cursor = None
        aocs_list = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM aocs ORDER BY data_criacao DESC, id DESC"
            cursor.execute(sql)
            all_data = cursor.fetchall()
            aocs_list = [self._map_row_to_model(row) for row in all_data if row]
            aocs_list = [aocs for aocs in aocs_list if aocs is not None]
            return aocs_list
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar AOCS: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def update(self, id: int, aocs_req: AocsUpdateRequest) -> Aocs | None:
        cursor = None
        fields_to_update = []
        params = []
        resolved_fks = {} 

        try:
            if aocs_req.unidade_requisitante_nome is not None:
                uni = self.unidade_repo.get_or_create(aocs_req.unidade_requisitante_nome)
                resolved_fks['id_unidade_requisitante'] = uni.id
                fields_to_update.append("id_unidade_requisitante = %s")
                params.append(uni.id)

            if aocs_req.local_entrega_descricao is not None:
                loc = self.local_repo.get_or_create(aocs_req.local_entrega_descricao)
                resolved_fks['id_local_entrega'] = loc.id
                fields_to_update.append("id_local_entrega = %s")
                params.append(loc.id)

            if aocs_req.agente_responsavel_nome is not None:
                age = self.agente_repo.get_or_create(aocs_req.agente_responsavel_nome)
                resolved_fks['id_agente_responsavel'] = age.id
                fields_to_update.append("id_agente_responsavel = %s")
                params.append(age.id)

            if aocs_req.dotacao_info_orcamentaria is not None:
                dot = self.dotacao_repo.get_or_create(aocs_req.dotacao_info_orcamentaria)
                resolved_fks['id_dotacao'] = dot.id
                fields_to_update.append("id_dotacao = %s")
                params.append(dot.id)

            if aocs_req.numero_aocs is not None:
                fields_to_update.append("numero_aocs = %s")
                params.append(aocs_req.numero_aocs)
            if aocs_req.data_criacao is not None:
                fields_to_update.append("data_criacao = %s")
                params.append(aocs_req.data_criacao)
            if aocs_req.justificativa is not None:
                fields_to_update.append("justificativa = %s")
                params.append(aocs_req.justificativa)
            if aocs_req.numero_pedido is not None:
                fields_to_update.append("numero_pedido = %s")
                params.append(aocs_req.numero_pedido)
            if aocs_req.empenho is not None:
                fields_to_update.append("empenho = %s")
                params.append(aocs_req.empenho)

            if not fields_to_update:
                logger.warning(f"Tentativa de atualizar AOCS ID {id} sem dados para alterar.")
                return self.get_by_id(id) 

            params.append(id) 

            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            set_clause = ", ".join(fields_to_update)
            sql = f"UPDATE aocs SET {set_clause} WHERE id = %s RETURNING *"

            cursor.execute(sql, params) 
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_aocs = self._map_row_to_model(updated_data)
            if updated_aocs:
                 logger.info(f"AOCS ID {id} ('{updated_aocs.numero_aocs}') atualizada.")
            else:
                 logger.warning(f"Tentativa de atualizar AOCS ID {id} falhou (não encontrado).")
            return updated_aocs

        except (ValueError, Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             if isinstance(error, ValueError):
                 logger.warning(f"Erro ao resolver FKs durante atualização da AOCS ID {id} (Req: {aocs_req}): {error}")
             else:
                 logger.exception(f"Erro inesperado ao atualizar AOCS ID {id} (Req: {aocs_req}): {error}")
             raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        aocs_para_deletar = self.get_by_id(id)
        if not aocs_para_deletar:
             logger.warning(f"Tentativa de deletar AOCS ID {id} falhou (não encontrada).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM aocs WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"AOCS ID {id} ('{aocs_para_deletar.numero_aocs}') deletada (Pedidos associados podem ter sido deletados via CASCADE).")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error: 
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar AOCS ID {id} ('{aocs_para_deletar.numero_aocs}'). Provavelmente ainda possui Pedidos vinculados (sem CASCADE).")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar AOCS ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()