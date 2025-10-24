from datetime import date
from pydantic import BaseModel

class AnexosBase(BaseModel):
    tipo_documento: str | None
    tipo_entidade: str
    
class AnexosRequest(AnexosBase):
    entidade_nome: str  

class AnexosResponse(AnexosBase):
    id: int
    nome_original: str
    nome_seguro: str
    data_upload: date
    id_entidade: int

    class Config:
        from_attributes = True