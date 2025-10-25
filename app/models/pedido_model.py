from datetime import date
from decimal import Decimal

class Pedido: 
    def __init__(self,
                 id: int,
                 id_item_contrato: int,
                 id_aocs: int,
                 quantidade_pedida: Decimal,
                 data_pedido: date, 
                 status_entrega: str, 
                 quantidade_entregue: Decimal):
        self.id: int = id
        self.id_item_contrato: int = id_item_contrato
        self.id_aocs: int = id_aocs
        self.quantidade_pedida: Decimal = quantidade_pedida
        self.data_pedido: date = data_pedido
        self.status_entrega: str = status_entrega
        self.quantidade_entregue: Decimal = quantidade_entregue