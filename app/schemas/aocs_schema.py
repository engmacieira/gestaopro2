from datetime import date
from pydantic import BaseModel, Field, ConfigDict 

class AocsBase(BaseModel):
    numero_aocs: str 
    data_criacao: date = Field(default_factory=date.today) 
    justificativa: str   
    numero_pedido: str | None = None
    empenho: str | None = None

class AocsCreateRequest(AocsBase): 
    unidade_requisitante_nome: str
    local_entrega_descricao: str 
    agente_responsavel_nome: str
    dotacao_info_orcamentaria: str 

class AocsUpdateRequest(BaseModel):
    numero_aocs: str | None = None
    data_criacao: date | None = None
    justificativa: str | None = None
    numero_pedido: str | None = None
    empenho: str | None = None
    unidade_requisitante_nome: str | None = None
    local_entrega_descricao: str | None = None
    agente_responsavel_nome: str | None = None
    dotacao_info_orcamentaria: str | None = None

class AocsResponse(AocsBase):
    id: int
    id_unidade_requisitante: int
    id_local_entrega: int
    id_agente_responsavel: int
    id_dotacao: int

    model_config = ConfigDict(from_attributes=True)