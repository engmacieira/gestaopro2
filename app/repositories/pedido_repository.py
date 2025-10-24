import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from datetime import date
from app.models.pedido_model import Pedido
from app.schemas.pedido_schema import PedidoRequest
from .item_repository import ItemRepository
from .aocs_repository import AocsRepository

class PedidoRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn
        self.itens_repo = ItemRepository(db_conn)
        self.aocs_repo = AocsRepository(db_conn)

    #Mapear
    def _map_row_to_model(self, row: DictCursor) -> Pedido:

    #Monta a AOCS
        return Pedido(
            id=row['id'],
            id_item_contrato=row['id_item_contrato'],
            id_aocs=row['id_aocs'],
            quantidade_pedida=row['quantidade_pedida'],
            data_pedido=row['data_pedido'],
            status_entrega=row['status_entrega'],
            quantidade_entregue=row['quantidade_entregue'],
        )
    
    #Criar
    def create(self, pedidos_req: PedidoRequest) -> Pedido:
        cursor = None
        try:
            #repositório
            ite = self.itens_repo.get_by_descricao(pedidos_req.item_contrato_nome)
            aoc = self.aocs_repo.get_by_aocs(pedidos_req.aocs_nome)
                        
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO pedidos (id_item_contrato, id_aocs, quantidade_pedida, data_pedido, status_entrega, quantidade_entregue)
                VALUES (%s, %s, %s, %s, %s, %s) 
                RETURNING * """
                        
            cursor.execute(sql, (ite.id, aoc.id, pedidos_req.quantidade_pedida, pedidos_req.data_pedido, pedidos_req.status_entrega, pedidos_req.quantidade_entregue))
            new_data = cursor.fetchone()
            self.db_conn.commit()
            
            return self._map_row_to_model(new_data)
        
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn:
                self.db_conn.rollback() 
            print(f"Erro ao criar pedidos: {error}")
            raise 
        
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Pedido | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM pedidos WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return self._map_row_to_model(data)
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #ListarGeral
    def get_all(self) -> list[Pedido]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
        
            sql = "SELECT * FROM pedidos ORDER BY id_item_contrato"
        
            cursor.execute(sql)
    
            all_data = cursor.fetchall()
        
            return [self._map_row_to_model(row)
                    for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Atualizar
    def update(self, id: int, pedidos_req: PedidoRequest) -> Pedido | None:
        cursor = None
        try:
            #repositório
            ite = self.itens_repo.get_by_descricao(pedidos_req.item_contrato_nome)
            aoc = self.aocs_repo.get_by_aocs(pedidos_req.aocs_nome)
            
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE pedidos 
                SET 
                    id_item_contrato = %s, 
                    id_aocs = %s, 
                    quantidade_pedida = %s, 
                    data_pedido = %s, 
                    status_entrega = %s, 
                    quantidade_entregue = %s
                WHERE id = %s
                RETURNING *
            """
            
            params = (ite.id, aoc.id, pedidos_req.quantidade_pedida, pedidos_req.data_pedido, pedidos_req.status_entrega, pedidos_req.quantidade_entregue, id)
            
            cursor.execute(sql, (params))
            updated_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            if updated_data:
                return self._map_row_to_model(updated_data)
            
            return None
        
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn:
                self.db_conn.rollback()
            print(f"Erro ao atualizar contrato: {error}")
            raise
        
        finally:
            if cursor:
                cursor.close()

    #Excluir
    def delete(self, id: int) -> bool:
        cursor = None
        try:
            cursor = self.db_conn.cursor()
            
            sql = "DELETE FROM pedidos WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()