import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from datetime import date
import logging
from app.models.ci_pagamento_model import CiPagamento 
from app.schemas.ci_pagamento_schema import CiPagamentoCreateRequest, CiPagamentoUpdateRequest 
from .aocs_repository import AocsRepository
from .agente_repository import AgenteRepository
from .unidade_repository import UnidadeRepository
from .dotacao_repository import DotacaoRepository

logger = logging.getLogger(__name__)

class CiPagamentoRepository: 
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn
        self.aocs_repo = AocsRepository(db_conn)
        self.agente_repo = AgenteRepository(db_conn)
        self.unidade_repo = UnidadeRepository(db_conn)
        self.dotacao_repo = DotacaoRepository(db_conn)

    def _map_row_to_model(self, row: DictCursor | None) -> CiPagamento | None:
        if not row:
            return None
        try:
            return CiPagamento(
                id=row['id'],
                id_aocs=row['id_aocs'],
                id_pedido=row['id_pedido'],
                numero_ci=row['numero_ci'],
                data_ci=row['data_ci'],
                numero_nota_fiscal=row['numero_nota_fiscal'],
                serie_nota_fiscal=row.get('serie_nota_fiscal'), 
                codigo_acesso_nota=row.get('codigo_acesso_nota'),
                data_nota_fiscal=row['data_nota_fiscal'],
                valor_nota_fiscal=row['valor_nota_fiscal'],
                id_dotacao_pagamento=row['id_dotacao_pagamento'],
                observacoes_pagamento=row.get('observacoes_pagamento'),
                id_solicitante=row['id_solicitante'],
                id_secretaria=row['id_secretaria']
            )
        except KeyError as e:
            logger.error(f"Erro de mapeamento CI Pagamento: Coluna '{e}' não encontrada.")
            return None

    def create(self, ci_req: CiPagamentoCreateRequest, id_pedido: int) -> CiPagamento:
        cursor = None
        try:
            aoc = self.aocs_repo.get_by_numero_aocs(ci_req.aocs_numero) 
            if not aoc: raise ValueError(f"AOCS '{ci_req.aocs_numero}' não encontrada.")

            age = self.agente_repo.get_by_nome(ci_req.solicitante_nome)
            if not age: raise ValueError(f"Agente '{ci_req.solicitante_nome}' não encontrado.")

            uni = self.unidade_repo.get_by_nome(ci_req.secretaria_nome)
            if not uni: raise ValueError(f"Unidade '{ci_req.secretaria_nome}' não encontrada.")

            dot = self.dotacao_repo.get_by_info_orcamentaria(ci_req.dotacao_info_orcamentaria) 
            if not dot: raise ValueError(f"Dotação '{ci_req.dotacao_info_orcamentaria}' não encontrada.")

            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = """
                INSERT INTO ci_pagamento (id_aocs, numero_ci, data_ci, numero_nota_fiscal,
                                          serie_nota_fiscal, codigo_acesso_nota, data_nota_fiscal,
                                          valor_nota_fiscal, id_dotacao_pagamento,
                                          observacoes_pagamento, id_solicitante, id_secretaria, id_pedido)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """
            params = (
                aoc.id, ci_req.numero_ci, ci_req.data_ci, ci_req.numero_nota_fiscal,
                ci_req.serie_nota_fiscal, ci_req.codigo_acesso_nota, ci_req.data_nota_fiscal,
                ci_req.valor_nota_fiscal, dot.id, ci_req.observacoes_pagamento,
                age.id, uni.id, id_pedido
            )
            cursor.execute(sql, params)
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_ci = self._map_row_to_model(new_data)
            if not new_ci:
                logger.error("Falha ao mapear dados da CI Pagamento recém-criada.")
                raise Exception("Falha ao mapear dados da CI Pagamento recém-criada.")

            logger.info(f"CI Pagamento criada com ID {new_ci.id} (Num: '{new_ci.numero_ci}') para AOCS ID {aoc.id}")
            return new_ci

        except (ValueError, Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            if isinstance(error, ValueError):
                 logger.warning(f"Erro ao resolver FKs durante criação da CI (Req: {ci_req}): {error}")
            elif isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao criar CI (Num CI/NF duplicado?) (Req: {ci_req}): {error}")
            else:
                 logger.exception(f"Erro inesperado ao criar CI (Req: {ci_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> CiPagamento | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM ci_pagamento WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar CI Pagamento por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_by_pedido_id(self, id_pedido: int) -> CiPagamento | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM ci_pagamento WHERE id_pedido = %s"
            
            cursor.execute(sql, (id_pedido,))
            data = cursor.fetchone()
            
            return self._map_row_to_model(data) 
            
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar CI Pagamento por Pedido ID ({id_pedido}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_all(self) -> list[CiPagamento]:
        cursor = None
        ci_list = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM ci_pagamento ORDER BY data_ci DESC, id DESC" 
            cursor.execute(sql)
            all_data = cursor.fetchall()
            ci_list = [self._map_row_to_model(row) for row in all_data if row]
            ci_list = [ci for ci in ci_list if ci is not None]
            return ci_list
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar CIs de Pagamento: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def update(self, id: int, ci_req: CiPagamentoUpdateRequest) -> CiPagamento | None:
        cursor = None
        fields_to_update = []
        params = []
        resolved_fks = {}

        try:
            if ci_req.aocs_numero is not None:
                aoc = self.aocs_repo.get_by_numero_aocs(ci_req.aocs_numero)
                if not aoc: raise ValueError(f"AOCS '{ci_req.aocs_numero}' não encontrada.")
                resolved_fks['id_aocs'] = aoc.id
                fields_to_update.append("id_aocs = %s")
                params.append(aoc.id)
            
            if ci_req.solicitante_nome is not None:
                age = self.agente_repo.get_by_nome(ci_req.solicitante_nome)
                if not age: raise ValueError(f"Agente '{ci_req.solicitante_nome}' não encontrado.")
                resolved_fks['id_solicitante'] = age.id
                fields_to_update.append("id_solicitante = %s")
                params.append(age.id)
            
            if ci_req.secretaria_nome is not None:
                uni = self.unidade_repo.get_by_nome(ci_req.secretaria_nome)
                if not uni: raise ValueError(f"Unidade '{ci_req.secretaria_nome}' não encontrada.")
                resolved_fks['id_secretaria'] = uni.id
                fields_to_update.append("id_secretaria = %s")
                params.append(uni.id)
            
            if ci_req.dotacao_info_orcamentaria is not None:
                dot = self.dotacao_repo.get_by_info_orcamentaria(ci_req.dotacao_info_orcamentaria)
                if not dot: raise ValueError(f"Dotação '{ci_req.dotacao_info_orcamentaria}' não encontrada.")
                resolved_fks['id_dotacao_pagamento'] = dot.id
                fields_to_update.append("id_dotacao_pagamento = %s")
                params.append(dot.id)

            schema_to_col = {
                'numero_ci': 'numero_ci', 'data_ci': 'data_ci',
                'numero_nota_fiscal': 'numero_nota_fiscal',
                'serie_nota_fiscal': 'serie_nota_fiscal',
                'codigo_acesso_nota': 'codigo_acesso_nota',
                'data_nota_fiscal': 'data_nota_fiscal',
                'valor_nota_fiscal': 'valor_nota_fiscal',
                'observacoes_pagamento': 'observacoes_pagamento',
            }
            for field_name, value in ci_req.model_dump(exclude_unset=True).items():
                 if value is not None and field_name not in resolved_fks and field_name in schema_to_col:
                     db_col_name = schema_to_col[field_name]
                     fields_to_update.append(f"{db_col_name} = %s")
                     params.append(value)


            if not fields_to_update:
                logger.warning(f"Tentativa de atualizar CI Pagamento ID {id} sem dados para alterar.")
                return self.get_by_id(id)

            params.append(id) 

            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            set_clause = ", ".join(fields_to_update)
            sql = f"UPDATE ci_pagamento SET {set_clause} WHERE id = %s RETURNING *"

            cursor.execute(sql, params)
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_ci = self._map_row_to_model(updated_data)
            if updated_ci:
                 logger.info(f"CI Pagamento ID {id} ('{updated_ci.numero_ci}') atualizada.")
            else:
                 logger.warning(f"Tentativa de atualizar CI Pagamento ID {id} falhou (não encontrado).")
            return updated_ci

        except (ValueError, Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             if isinstance(error, ValueError):
                 logger.warning(f"Erro ao resolver FKs/Validar dados durante atualização da CI ID {id} (Req: {ci_req}): {error}")
             elif isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao atualizar CI ID {id} (Num CI/NF duplicado?) (Req: {ci_req}): {error}")
             else:
                 logger.exception(f"Erro inesperado ao atualizar CI ID {id} (Req: {ci_req}): {error}")
             raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        ci_para_deletar = self.get_by_id(id)
        if not ci_para_deletar:
             logger.warning(f"Tentativa de deletar CI Pagamento ID {id} falhou (não encontrada).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM ci_pagamento WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"CI Pagamento ID {id} ('{ci_para_deletar.numero_ci}') deletada.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error: 
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar CI ID {id}.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar CI ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()