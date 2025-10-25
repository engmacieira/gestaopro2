from decimal import Decimal
from .descricao_item_vo import DescricaoItem 

class Item:
    def __init__(self,
                 id: int,
                 id_contrato: int,
                 numero_item: int,
                 descricao_obj: DescricaoItem, 
                 unidade_medida: str,
                 quantidade: Decimal,
                 valor_unitario: Decimal,
                 ativo: bool,
                 marca: str | None = None):
        self.id: int = id
        self.id_contrato: int = id_contrato
        self.numero_item: int = numero_item
        self.descricao: DescricaoItem = descricao_obj 
        self.marca: str | None = marca
        self.unidade_medida: str = unidade_medida
        self.quantidade: Decimal = quantidade
        self.valor_unitario: Decimal = valor_unitario
        self.ativo: bool = ativo