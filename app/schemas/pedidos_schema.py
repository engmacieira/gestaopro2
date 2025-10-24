from datetime import date
from pydantic import BaseModel
from decimal import Decimal

class PedidosBase(BaseModel):
    quantidade_pedida: Decimal
    data_pedido: date
    status_entrega: str
    quantidade_entregue: Decimal
    
class PedidosRequest(PedidosBase):
    item_contrato_nome: str
    aocs_nome: str

class PedidosResponse(PedidosBase):
    id: int
    id_item_contrato: int
    id_aocs: int

    class Config:
        from_attributes = True