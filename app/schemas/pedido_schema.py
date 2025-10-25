from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class PedidoBase(BaseModel):
    quantidade_pedida: Decimal = Field(..., gt=0) 
    status_entrega: str = "Pendente" 
    quantidade_entregue: Decimal = Decimal('0.0') 

class PedidoCreateRequest(BaseModel): 
    item_contrato_id: int
    quantidade_pedida: Decimal = Field(..., gt=0)
    
class PedidoUpdateRequest(BaseModel): 
    status_entrega: str | None = None
    quantidade_entregue: Decimal | None = None
    
class PedidoResponse(PedidoBase):
    id: int
    id_item_contrato: int
    id_aocs: int
    data_pedido: date 
    
    class Config:
        from_attributes = True 