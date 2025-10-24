from decimal import Decimal
from pydantic import BaseModel
from .descricaoitem_schema import DescricaoitemRequest, DescricaoitemResponse

class ItensBase(BaseModel):
    numero_item: int
    marca: str | None = None
    unidade_medida: str
    quantidade: Decimal
    valor_unitario: Decimal  
    
class ItensRequest(ItensBase):
    contrato_nome: str
    descricao: DescricaoitemRequest 

class ItensResponse(ItensBase):
    id: int
    ativo: bool
    id_contrato: int
    descricao: DescricaoitemResponse

    class Config:
        from_attributes = True