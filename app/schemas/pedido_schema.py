from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

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
    
    model_config = ConfigDict(from_attributes=True)
    
class RegistrarEntregaRequest(BaseModel):
    quantidade: Decimal = Field(..., gt=0)
    data_entrega: date
    nota_fiscal: str
    
class EntregaItemLote(BaseModel):
    id_pedido: int
    quantidade: Decimal = Field(..., gt=0)

class RegistrarEntregaLoteRequest(BaseModel):
    data_entrega: date
    nota_fiscal: str
    itens: list[EntregaItemLote]