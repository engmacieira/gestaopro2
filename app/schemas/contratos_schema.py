from datetime import date
from pydantic import BaseModel
from .fornecedor_schema import FornecedorRequest, FornecedorResponse

class ContratosBase(BaseModel):
    numero_contrato: str
    data_inicio: date  
    data_fim: date 

    
class ContratosRequest(ContratosBase):
    fornecedor: FornecedorRequest
    categoria_nome: str
    instrumento_nome: str
    modalidade_nome: str
    numero_modalidade_nome: str
    processo_licitatorio_nome: str


class ContratosResponse(ContratosBase):
    id: int
    data_criacao: date
    ativo: bool
    fornecedor: FornecedorResponse
    id_categoria: int
    id_instrumento_contratual: int
    id_modalidade: int
    id_numero_modalidade: int
    id_processo_licitatorio: int

    class Config:
        from_attributes = True