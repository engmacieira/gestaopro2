import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from datetime import date
import logging
from app.models.contrato_model import Contrato
from app.models.fornecedor_vo import Fornecedor
from app.schemas.contrato_schema import ContratoCreateRequest, ContratoUpdateRequest
from .categoria_repository import CategoriaRepository
from .instrumento_repository import InstrumentoRepository
from .modalidade_repository import ModalidadeRepository
from .numero_modalidade_repository import NumeroModalidadeRepository
from .processo_licitatorio_repository import ProcessoLicitatorioRepository

logger = logging.getLogger(__name__)

class ContratoRepository: 
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn
        self.categoria_repo = CategoriaRepository(db_conn)
        self.instrumento_repo = InstrumentoRepository(db_conn)
        self.modalidade_repo = ModalidadeRepository(db_conn)
        self.numeromodalidade_repo = NumeroModalidadeRepository(db_conn)
        self.processolicitatorio_repo = ProcessoLicitatorioRepository(db_conn)

    def _map_row_to_model(self, row: DictCursor | None) -> Contrato | None:
        if not row:
            return None
        try:
            fornecedor_obj = Fornecedor(
                nome=row['fornecedor'],
                cpf_cnpj=row.get('cpf_cnpj'),
                email=row.get('email'),
                telefone=row.get('telefone')
            )
            return Contrato(
                id=row['id'],
                id_categoria=row['id_categoria'],
                numero_contrato=row['numero_contrato'],
                data_inicio=row['data_inicio'],
                data_fim=row['data_fim'],
                data_criacao=row['data_criacao'],
                ativo=row['ativo'],
                id_instrumento_contratual=row['id_instrumento_contratual'],
                id_modalidade=row['id_modalidade'],
                id_numero_modalidade=row['id_numero_modalidade'],
                id_processo_licitatorio=row['id_processo_licitatorio'],
                fornecedor_obj=fornecedor_obj 
            )
        except KeyError as e:
            logger.error(f"Erro de mapeamento Contrato: Coluna '{e}' não encontrada.")
            return None

    def create(self, contrato_req: ContratoCreateRequest) -> Contrato:
        cursor = None
        try:
            cat = self.categoria_repo.get_by_nome(contrato_req.categoria_nome)
            if not cat:
                raise ValueError(f"Categoria '{contrato_req.categoria_nome}' não encontrada.")
            
            inst = self.instrumento_repo.get_by_nome(contrato_req.instrumento_nome)
            if not inst:
                raise ValueError(f"Instrumento '{contrato_req.instrumento_nome}' não encontrado.")
            
            mod = self.modalidade_repo.get_by_nome(contrato_req.modalidade_nome)
            if not mod:
                raise ValueError(f"Modalidade '{contrato_req.modalidade_nome}' não encontrada.")
            
            num_mod = self.numeromodalidade_repo.get_by_numero_ano(contrato_req.numero_modalidade_str)
            if not num_mod:
                raise ValueError(f"Número/Ano da Modalidade '{contrato_req.numero_modalidade_str}' não encontrado.")
            
            proc = self.processolicitatorio_repo.get_by_numero(contrato_req.processo_licitatorio_numero)
            if not proc:
                raise ValueError(f"Processo Licitatório '{contrato_req.processo_licitatorio_numero}' não encontrado.")
            
            forn_req = contrato_req.fornecedor
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = """
                INSERT INTO contratos (id_categoria, numero_contrato, fornecedor, cpf_cnpj, email, telefone,
                    data_inicio, data_fim, data_criacao, ativo, id_instrumento_contratual, id_modalidade,
                    id_numero_modalidade, id_processo_licitatorio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """
            params = (
                cat.id, contrato_req.numero_contrato, forn_req.nome, forn_req.cpf_cnpj, forn_req.email, forn_req.telefone,
                contrato_req.data_inicio, contrato_req.data_fim, date.today(), True,
                inst.id, mod.id, num_mod.id, proc.id
            )
            cursor.execute(sql, params)
            new_data = cursor.fetchone()
            self.db_conn.commit()
            new_contrato = self._map_row_to_model(new_data)
            
            if not new_contrato:
                logger.error("Falha ao mapear dados do contrato recém-criado.")
                raise Exception("Falha ao mapear dados do contrato recém-criado.")

            logger.info(f"Contrato criado com ID {new_contrato.id} ('{new_contrato.numero_contrato}')")
            return new_contrato

        except (ValueError, Exception, psycopg2.DatabaseError) as error:

            if self.db_conn: self.db_conn.rollback()
            if isinstance(error, ValueError):
                 logger.warning(f"Erro ao resolver FKs durante criação do Contrato (Req: {contrato_req}): {error}")
            elif isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao criar Contrato (Num. Contrato duplicado?) (Req: {contrato_req}): {error}")
            else:
                 logger.exception(f"Erro inesperado ao criar Contrato (Req: {contrato_req}): {error}")
            raise

        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> Contrato | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM contratos WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar Contrato por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_by_numero_contrato(self, numero_contrato: str) -> Contrato | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM contratos WHERE numero_contrato = %s"
            cursor.execute(sql, (numero_contrato,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar Contrato por Numero ('{numero_contrato}'): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_all(self, mostrar_inativos: bool = False) -> list[Contrato]:
        cursor = None
        contratos_list = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM contratos"
            if not mostrar_inativos:
                sql += " WHERE ativo = TRUE"
            sql += " ORDER BY data_fim DESC, numero_contrato"
            cursor.execute(sql)
            all_data = cursor.fetchall()
            contratos_list = [self._map_row_to_model(row) for row in all_data if row]
            contratos_list = [c for c in contratos_list if c is not None]
            return contratos_list
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar Contratos (Inativos: {mostrar_inativos}): {error}")
             return []
        finally:
            if cursor: cursor.close()

    def update(self, id: int, contrato_req: ContratoUpdateRequest) -> Contrato | None:
        cursor = None
        fields_to_update = []
        params = []
        resolved_fks = {}

        try:
            if contrato_req.categoria_nome is not None:
                cat = self.categoria_repo.get_by_nome(contrato_req.categoria_nome)
                resolved_fks['id_categoria'] = cat.id
                fields_to_update.append("id_categoria = %s")
                params.append(cat.id)
            if contrato_req.instrumento_nome is not None:
                inst = self.instrumento_repo.get_by_nome(contrato_req.instrumento_nome)
                resolved_fks['id_instrumento_contratual'] = inst.id
                fields_to_update.append("id_instrumento_contratual = %s")
                params.append(inst.id)
            if contrato_req.modalidade_nome is not None:
                 mod = self.modalidade_repo.get_by_nome(contrato_req.modalidade_nome)
                 resolved_fks['id_modalidade'] = mod.id
                 fields_to_update.append("id_modalidade = %s")
                 params.append(mod.id)
            if contrato_req.numero_modalidade_str is not None:
                 num_mod = self.numeromodalidade_repo.get_by_numero_ano(contrato_req.numero_modalidade_str)
                 resolved_fks['id_numero_modalidade'] = num_mod.id
                 fields_to_update.append("id_numero_modalidade = %s")
                 params.append(num_mod.id)
            if contrato_req.processo_licitatorio_numero is not None:
                 proc = self.processolicitatorio_repo.get_by_numero(contrato_req.processo_licitatorio_numero)
                 resolved_fks['id_processo_licitatorio'] = proc.id
                 fields_to_update.append("id_processo_licitatorio = %s")
                 params.append(proc.id)

            if contrato_req.numero_contrato is not None:
                fields_to_update.append("numero_contrato = %s")
                params.append(contrato_req.numero_contrato)
            if contrato_req.data_inicio is not None:
                fields_to_update.append("data_inicio = %s")
                params.append(contrato_req.data_inicio)
            if contrato_req.data_fim is not None:
                fields_to_update.append("data_fim = %s")
                params.append(contrato_req.data_fim)
            if contrato_req.ativo is not None:
                fields_to_update.append("ativo = %s")
                params.append(contrato_req.ativo)

            if contrato_req.fornecedor is not None:
                forn_req = contrato_req.fornecedor
                if forn_req.nome is not None: 
                    fields_to_update.append("fornecedor = %s")
                    params.append(forn_req.nome)
                if forn_req.cpf_cnpj is not None:
                     fields_to_update.append("cpf_cnpj = %s")
                     params.append(forn_req.cpf_cnpj)
                if forn_req.email is not None:
                     fields_to_update.append("email = %s")
                     params.append(forn_req.email)
                if forn_req.telefone is not None:
                     fields_to_update.append("telefone = %s")
                     params.append(forn_req.telefone)


            if not fields_to_update:
                logger.warning(f"Tentativa de atualizar Contrato ID {id} sem dados para alterar.")
                return self.get_by_id(id)

            params.append(id) 

            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            set_clause = ", ".join(fields_to_update)
            sql = f"UPDATE contratos SET {set_clause} WHERE id = %s RETURNING *"

            cursor.execute(sql, params) 
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_contrato = self._map_row_to_model(updated_data)
            if updated_contrato:
                 logger.info(f"Contrato ID {id} ('{updated_contrato.numero_contrato}') atualizado.")
            else:
                 logger.warning(f"Tentativa de atualizar Contrato ID {id} falhou (não encontrado).")
            return updated_contrato

        except (ValueError, Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             if isinstance(error, ValueError):
                 logger.warning(f"Erro ao resolver FKs/Validar dados durante atualização Contrato ID {id} (Req: {contrato_req}): {error}")
             elif isinstance(error, psycopg2.IntegrityError):
                  logger.warning(f"Erro de integridade ao atualizar Contrato ID {id} (Num Contrato duplicado?) (Req: {contrato_req}): {error}")
             else:
                 logger.exception(f"Erro inesperado ao atualizar Contrato ID {id} (Req: {contrato_req}): {error}")
             raise
        finally:
            if cursor: cursor.close()

    def set_active_status(self, id: int, status: bool) -> Contrato | None:
        cursor = None
        contrato_original = self.get_by_id(id)
        if not contrato_original:
            logger.warning(f"Tentativa de alterar status do contrato ID {id} falhou (não encontrado).")
            return None

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE contratos SET ativo = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (status, id))
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_contrato = self._map_row_to_model(updated_data)
            if updated_contrato:
                action = "ativado" if status else "desativado"
                logger.info(f"Contrato ID {id} ('{updated_contrato.numero_contrato}') foi {action}.")
            else:
                logger.error(f"Falha ao mapear contrato ID {id} após alteração de status.")
            return updated_contrato

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao alterar status do contrato ID {id} para {status}: {error}")
            raise
        finally:
            if cursor: cursor.close()


    def delete(self, id: int) -> bool:
        cursor = None
        contrato_para_deletar = self.get_by_id(id)
        if not contrato_para_deletar:
             logger.warning(f"Tentativa de deletar Contrato ID {id} falhou (não encontrado).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM contratos WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"Contrato ID {id} ('{contrato_para_deletar.numero_contrato}') deletado.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error:
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar Contrato ID {id} ('{contrato_para_deletar.numero_contrato}'). Vinculado a ItensContrato.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar Contrato ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()