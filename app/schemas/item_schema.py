from decimal import Decimal
from pydantic import BaseModel
from .descricao_item_schema import DescricaoItemRequest, DescricaoItemResponse 

class ItemBase(BaseModel): 
    numero_item: int
    marca: str | None = None
    unidade_medida: str
    quantidade: Decimal
    valor_unitario: Decimal

class ItemRequest(ItemBase): 
    contrato_nome: str
    descricao: DescricaoItemRequest 

class ItemResponse(ItemBase): 
    id: int
    ativo: bool
    id_contrato: int
    descricao: DescricaoItemResponse 

    class Config:
        from_attributes = True