import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from datetime import date
from decimal import Decimal 
import logging
from app.models.pedido_model import Pedido 
from app.schemas.pedido_schema import PedidoCreateRequest, PedidoUpdateRequest 
from .item_repository import ItemRepository 
from .aocs_repository import AocsRepository 

logger = logging.getLogger(__name__)

class PedidoRepository: 
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn
        self.item_repo = ItemRepository(db_conn)
        self.aocs_repo = AocsRepository(db_conn)

    def _map_row_to_model(self, row: DictCursor | None) -> Pedido | None:
        if not row:
            return None
        try:
            return Pedido(
                id=row['id'],
                id_item_contrato=row['id_item_contrato'],
                id_aocs=row['id_aocs'],
                quantidade_pedida=row['quantidade_pedida'],
                status_entrega=row['status_entrega'],
                quantidade_entregue=row['quantidade_entregue'],
                data_pedido=row['data_pedido']
            )
        except KeyError as e:
            logger.error(f"Erro de mapeamento Pedido: Coluna '{e}' não encontrada.")
            return None

    def get_total_requested_quantity(self, id_item_contrato: int, exclude_pedido_id: int | None = None) -> Decimal:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = """
                SELECT COALESCE(SUM(quantidade_pedida), 0) AS total_reservado
                FROM pedidos
                WHERE id_item_contrato = %s
                  AND status_entrega != 'Cancelado' 
            """
            params = [id_item_contrato]

            if exclude_pedido_id is not None:
                sql += " AND id != %s"
                params.append(exclude_pedido_id)

            cursor.execute(sql, params)
            total_reservado = cursor.fetchone()['total_reservado']
            
            return total_reservado if isinstance(total_reservado, Decimal) else Decimal(str(total_reservado or '0.0'))

        except Exception as error:
             logger.exception(f"Erro ao calcular quantidade pedida total para Item ID {id_item_contrato}: {error}")
             raise
        finally:
            if cursor: cursor.close()


    def create(self, id_aocs: int, pedido_create_req: PedidoCreateRequest) -> Pedido:
        cursor = None
        try:
            aocs = self.aocs_repo.get_by_id(id_aocs)
            if not aocs:
                raise ValueError(f"AOCS ID {id_aocs} não encontrada para adicionar pedido.")

            item = self.item_repo.get_by_id(pedido_create_req.item_contrato_id)
            if not item:
                raise ValueError(f"ItemContrato ID {pedido_create_req.item_contrato_id} não encontrado.")
            
            if not item.ativo:
                raise ValueError(f"Item de Contrato ID {item.id} não está ativo e não pode receber novos pedidos.")

            quantidade_pedida_decimal = pedido_create_req.quantidade_pedida 
            
            total_reservado = self.get_total_requested_quantity(item.id)
            
            quantidade_total_solicitada = total_reservado + quantidade_pedida_decimal
            
            if quantidade_total_solicitada > item.quantidade:
                saldo_disponivel = item.quantidade - total_reservado

                error_msg = (f"A quantidade pedida ({quantidade_pedida_decimal:.2f}) excede o saldo disponível "
                             f"do item. Total do Contrato: {item.quantidade:.2f}, Já reservado: {total_reservado:.2f}, "
                             f"Saldo: {saldo_disponivel:.2f}")
                logger.warning(error_msg)
                raise ValueError(error_msg)

            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = """
                INSERT INTO pedidos (id_item_contrato, id_aocs, quantidade_pedida,
                                   status_entrega, quantidade_entregue)
                                   -- data_pedido é obtido no RETURNING do JOIN com aocs
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *, %s AS data_pedido -- Adiciona data_pedido da AOCS ao RETURNING para mapeamento
            """
            status_inicial = "Pendente"
            qtd_entregue_inicial = Decimal('0.0') 
            params = (
                item.id,
                aocs.id,
                quantidade_pedida_decimal,
                status_inicial,
                qtd_entregue_inicial,
                aocs.data_criacao 
            )
            cursor.execute(sql, params)
            new_data = cursor.fetchone()
            self.db_conn.commit()

            new_pedido = self._map_row_to_model(new_data)
            if not new_pedido:
                logger.error("Falha ao mapear dados do pedido recém-criado.")
                raise Exception("Falha ao mapear dados do pedido recém-criado.")

            logger.info(f"Pedido criado com ID {new_pedido.id} (Item ID {item.id}) para AOCS ID {aocs.id}")
            return new_pedido

        except (ValueError, Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            if isinstance(error, ValueError):
                 logger.warning(f"Erro ao validar FKs/Saldo durante criação do Pedido (Req: {pedido_create_req}): {error}")
            elif isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao criar Pedido (Item já existe na AOCS?) (Req: {pedido_create_req}): {error}")
            else:
                 logger.exception(f"Erro inesperado ao criar Pedido (Req: {pedido_create_req}): {error}")
            raise
        finally:
            if cursor: cursor.close()

    def get_by_id(self, id: int) -> Pedido | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = """
                SELECT p.*, a.data_criacao as data_pedido
                FROM pedidos p
                JOIN aocs a ON p.id_aocs = a.id
                WHERE p.id = %s
            """
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            return self._map_row_to_model(data)
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao buscar Pedido por ID ({id}): {error}")
             return None
        finally:
            if cursor: cursor.close()

    def get_by_aocs_id(self, id_aocs: int) -> list[Pedido]:
        cursor = None
        pedidos_list = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = """
                SELECT p.*, a.data_criacao as data_pedido
                FROM pedidos p
                JOIN aocs a ON p.id_aocs = a.id
                WHERE p.id_aocs = %s
                ORDER BY p.id -- Ou pelo numero_item se fizer JOIN com itenscontrato
            """
            cursor.execute(sql, (id_aocs,))
            all_data = cursor.fetchall()
            pedidos_list = [self._map_row_to_model(row) for row in all_data if row]
            pedidos_list = [p for p in pedidos_list if p is not None]
            return pedidos_list
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar Pedidos para AOCS ID {id_aocs}: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def get_all(self) -> list[Pedido]:
        cursor = None
        pedidos_list = []
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = """
                SELECT p.*, a.data_criacao as data_pedido
                FROM pedidos p
                JOIN aocs a ON p.id_aocs = a.id
                ORDER BY p.id_aocs, p.id
            """
            cursor.execute(sql)
            all_data = cursor.fetchall()
            pedidos_list = [self._map_row_to_model(row) for row in all_data if row]
            pedidos_list = [p for p in pedidos_list if p is not None]
            return pedidos_list
        except (Exception, psycopg2.DatabaseError) as error:
             logger.exception(f"Erro inesperado ao listar todos os Pedidos: {error}")
             return []
        finally:
            if cursor: cursor.close()

    def update(self, id: int, pedido_req: PedidoUpdateRequest) -> Pedido | None:
        cursor = None
        fields_to_update = []
        params = []

        if pedido_req.status_entrega is not None:
            fields_to_update.append("status_entrega = %s")
            params.append(pedido_req.status_entrega)
        if pedido_req.quantidade_entregue is not None:
             fields_to_update.append("quantidade_entregue = %s")
             params.append(pedido_req.quantidade_entregue)
        
        if not fields_to_update:
            logger.warning(f"Tentativa de atualizar Pedido ID {id} sem dados para alterar.")
            return self.get_by_id(id) 

        params.append(id) 

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            set_clause = ", ".join(fields_to_update)
            sql = f"""
                UPDATE pedidos SET {set_clause}
                FROM aocs
                WHERE pedidos.id = %s AND pedidos.id_aocs = aocs.id
                RETURNING pedidos.*, aocs.data_criacao as data_pedido
            """
            cursor.execute(sql, params)
            updated_data = cursor.fetchone()
            self.db_conn.commit()

            updated_pedido = self._map_row_to_model(updated_data)
            if updated_pedido:
                 logger.info(f"Pedido ID {id} atualizado.") 
            else:
                 logger.warning(f"Tentativa de atualizar Pedido ID {id} falhou (não encontrado).")
            return updated_pedido

        except (ValueError, Exception, psycopg2.DatabaseError) as error: 
             if self.db_conn: self.db_conn.rollback()
             if isinstance(error, psycopg2.IntegrityError):
                 logger.warning(f"Erro de integridade ao atualizar Pedido ID {id} (Req: {pedido_req}): {error}")
             else:
                 logger.exception(f"Erro inesperado ao atualizar Pedido ID {id} (Req: {pedido_req}): {error}")
             raise
        finally:
            if cursor: cursor.close()

    def delete(self, id: int) -> bool:
        cursor = None
        pedido_para_deletar = self.get_by_id(id)
        if not pedido_para_deletar:
             logger.warning(f"Tentativa de deletar Pedido ID {id} falhou (não encontrado).")
             return False

        try:
            cursor = self.db_conn.cursor()
            sql = "DELETE FROM pedidos WHERE id = %s"
            cursor.execute(sql, (id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()

            if rowcount > 0:
                logger.info(f"Pedido ID {id} (Item ID: {pedido_para_deletar.id_item_contrato}, AOCS ID: {pedido_para_deletar.id_aocs}) deletado e saldo liberado.")
            return rowcount > 0

        except psycopg2.IntegrityError as fk_error: 
             if self.db_conn: self.db_conn.rollback()
             logger.warning(f"Erro de integridade ao deletar Pedido ID {id}.")
             raise fk_error
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro inesperado ao deletar Pedido ID {id}: {error}")
            raise error
        finally:
            if cursor: cursor.close()