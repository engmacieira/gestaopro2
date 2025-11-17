import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
import logging
from app.models.descricao_item_vo import DescricaoItem 
from app.models.item_model import Item 
from app.schemas.item_schema import ItemRequest 
from .contrato_repository import ContratoRepository

logger = logging.getLogger(__name__)

class ItemRepository: 
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn
        self.contrato_repo = ContratoRepository(db_conn)

    def _map_row_to_model(self, row: DictCursor | None) -> Item | None:
        if not row:
            return None
        try:
            descricao_obj = DescricaoItem(
                descricao=row['descricao']
            )
            return Item(
                id=row['id'],
                id_contrato=row['id_contrato'],
                numero_item=row['numero_item'], 
                unidade_medida=row['unidade_medida'],
                quantidade=row['quantidade'], 
                valor_unitario=row['valor_unitario'], 
                ativo=row['ativo'],
                marca=row.get('marca'),
                descricao_obj=descricao_obj 
            )
        except KeyError as e:
            logger.error(f"Erro de mapeamento Item: Coluna '{e}' não encontrada.")
            return None
        except Exception as e: 
             logger.error(f"Erro inesperado ao mapear Item (ID: {row.get('id')} se disponível): {e}")
             return None

    def create(self, item_req: ItemRequest) -> Item:
        cursor = None
        try:
            cont = self.contrato_repo.get_by_numero_contrato(item_req.contrato_nome)
            if not cont:
                raise ValueError(f"Contrato '{item_req.contrato_nome}' não encontrado.")

            desc_str = item_req.descricao.descricao

            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = """
                INSERT INTO itenscontrato (id_contrato, numero_item, descricao,
                                           unidade_medida, quantidade, valor_unitario,
                                           ativo, marca)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """
            params = (
                cont.id, item_req.numero_item, desc_str, 
                item_req.unidade_medida, item_req.quantidade, item_req.valor_unitario,
                True, item_req.marca 
            )
            cursor.execute(sql, params)
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_item = self._map_row_to_model(new_data)
            if not new_item:
                logger.error("Falha ao mapear dados do item recém-criado.")
                raise Exception("Falha ao mapear dados do item recém-criado.")

            logger.info(f"Item criado com ID {new_item.id} (Num: {new_item.numero_item}) para Contrato ID {cont.id}")
            return new_item

        except (ValueError, Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            if isinstance(error, ValueError):
                 logger.warning(f"Erro ao resolver FK Contrato durante criação do Item (Req: {item_req}): {error}")
            elif isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao criar Item (Num. Item duplicado no Contrato?) (Req: {item_req}): {error}")
            else:
                 logger.exception(f"Erro inesperado ao criar Item (Req: {item_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> Item | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM itenscontrato WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar Item por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_by_contrato_id(self, id_contrato: int) -> list[Item]:
        cursor = None
        items_list = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM itenscontrato WHERE id_contrato = %s ORDER BY numero_item"
            cursor.execute(sql, (id_contrato,))
            all_data = cursor.fetchall()
            items_list = [self._map_row_to_model(row) for row in all_data if row]
            items_list = [item for item in items_list if item is not None]
            return items_list
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar Itens para Contrato ID {id_contrato}: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def get_by_descricao(self, descricao: str) -> Item | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM itenscontrato WHERE descricao = %s LIMIT 1" 
            cursor.execute(sql, (descricao,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar Item por Descricao ('{descricao}'): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_all(self, mostrar_inativos: bool = False) -> list[Item]:
        cursor = None
        items_list = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM itenscontrato"
            if not mostrar_inativos:
                sql += " WHERE ativo = TRUE"
            sql += " ORDER BY id_contrato, numero_item" 
            cursor.execute(sql)
            all_data = cursor.fetchall()
            items_list = [self._map_row_to_model(row) for row in all_data if row]
            items_list = [item for item in items_list if item is not None]
            return items_list
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar todos os Itens (Inativos: {mostrar_inativos}): {error}")
             return []
        finally:
            if cursor: cursor.close()

    def update(self, id: int, item_req: ItemRequest) -> Item | None:
        cursor = None
        item_antigo = self.get_by_id(id) 
        if not item_antigo:
             logger.warning(f"Tentativa de atualizar Item ID {id} falhou (não encontrado).")
             return None

        try:
            cont = self.contrato_repo.get_by_numero_contrato(item_req.contrato_nome)
            if not cont:
                 raise ValueError(f"Contrato '{item_req.contrato_nome}' não encontrado para atualização do item.")

            desc_str = item_req.descricao.descricao

            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = """
                UPDATE itenscontrato
                SET
                    id_contrato = %s,
                    numero_item = %s,
                    descricao = %s,
                    unidade_medida = %s,
                    quantidade = %s,
                    valor_unitario = %s,
                    marca = %s
                    -- ativo = ?? <-- Lógica separada para ativar/desativar?
                WHERE id = %s
                RETURNING *
            """
            params = (
                cont.id, item_req.numero_item, desc_str,
                item_req.unidade_medida, item_req.quantidade, item_req.valor_unitario,
                item_req.marca,
                id 
            )
            cursor.execute(sql, params) 
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_item = self._map_row_to_model(updated_data)
            if updated_item:
                 logger.info(f"Item ID {id} (Contrato ID {cont.id}) atualizado.")
            return updated_item

        except (ValueError, Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             if isinstance(error, ValueError):
                 logger.warning(f"Erro ao resolver FK Contrato durante atualização do Item ID {id} (Req: {item_req}): {error}")
             elif isinstance(error, psycopg2.IntegrityError):
                  logger.warning(f"Erro de integridade ao atualizar Item ID {id} (Num. Item duplicado no Contrato?) (Req: {item_req}): {error}")
             else:
                 logger.exception(f"Erro inesperado ao atualizar Item ID {id} (Req: {item_req}): {error}")
             raise
        finally:
            if cursor: cursor.close()

    def set_active_status(self, id: int, status: bool) -> Item | None:
        cursor = None
        item_original = self.get_by_id(id)
        if not item_original:
            logger.warning(f"Tentativa de alterar status do item ID {id} falhou (não encontrado).")
            return None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "UPDATE itenscontrato SET ativo = %s WHERE id = %s RETURNING *"
            cursor.execute(sql, (status, id))
            updated_data = cursor.fetchone()
            self.db_conn.commit()
            updated_item = self._map_row_to_model(updated_data)
            if updated_item:
                action = "ativado" if status else "desativado"
                logger.info(f"Item ID {id} (Num: {updated_item.numero_item}) foi {action}.")
            else:
                 logger.error(f"Falha ao mapear item ID {id} após alteração de status.")
            return updated_item
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao alterar status do item ID {id} para {status}: {error}")
            raise
        finally:
            if cursor: cursor.close()


    def delete(self, id: int) -> bool:
        cursor = None
        item_para_deletar = self.get_by_id(id)
        if not item_para_deletar:
             logger.warning(f"Tentativa de deletar Item ID {id} falhou (não encontrado).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM itenscontrato WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"Item ID {id} (Num: {item_para_deletar.numero_item}, Contrato ID: {item_para_deletar.id_contrato}) deletado.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error:
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar Item ID {id} (Num: {item_para_deletar.numero_item}). Vinculado a Pedidos.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar Item ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()