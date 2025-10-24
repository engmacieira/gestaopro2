from datetime import date
from pydantic import BaseModel

class AocsBase(BaseModel):
    numero_aocs: str
    data_criacao: date   
    justificativa: str
    local_data: str
    numero_pedido: str | None = None
    tipo_pedido: str | None = None
    empenho: str | None = None
    
class AocsRequest(AocsBase):
    unidade_requisitante_nome: str
    local_entrega_nome: str
    agente_responsavel_nome: str  
    dotacao_nome: str

class AocsResponse(AocsBase):
    id: int
    id_unidade_requisitante: int
    id_local_entrega: int
    id_agente_responsavel: int  
    id_dotacao: int
 
    class Config:
        from_attributes = True