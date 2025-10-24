from decimal import Decimal
from pydantic import BaseModel
from .descricaoitem_schema import DescricaoitemRequest, DescricaoitemResponse

class ItemBase(BaseModel):
    numero_item: int
    marca: str | None = None
    unidade_medida: str
    quantidade: Decimal
    valor_unitario: Decimal  
    
class ItemRequest(ItemBase):
    contrato_nome: str
    descricao: DescricaoitemRequest 

class ItemResponse(ItemBase):
    id: int
    ativo: bool
    id_contrato: int
    descricao: DescricaoitemResponse

    class Config:
        from_attributes = True