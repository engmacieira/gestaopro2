from datetime import date
from pydantic import BaseModel, Field, ConfigDict 
from .fornecedor_schema import FornecedorRequest, FornecedorResponse

class ContratoBase(BaseModel): 
    numero_contrato: str
    data_inicio: date
    data_fim: date

class ContratoCreateRequest(ContratoBase):  
    fornecedor: FornecedorRequest 
    categoria_nome: str
    instrumento_nome: str
    modalidade_nome: str
    numero_modalidade_str: str
    processo_licitatorio_numero: str

class ContratoUpdateRequest(BaseModel): 
    numero_contrato: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    ativo: bool | None = None 
    fornecedor: FornecedorRequest | None = None 
    categoria_nome: str | None = None
    instrumento_nome: str | None = None
    modalidade_nome: str | None = None
    numero_modalidade_str: str | None = None
    processo_licitatorio_numero: str | None = None

class ContratoResponse(ContratoBase): 
    id: int
    data_criacao: date
    ativo: bool
    fornecedor: FornecedorResponse 
    id_categoria: int
    id_instrumento_contratual: int
    id_modalidade: int
    id_numero_modalidade: int
    id_processo_licitatorio: int

    model_config = ConfigDict(from_attributes=True)