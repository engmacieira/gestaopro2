from datetime import date
from pydantic import BaseModel

class AnexoBase(BaseModel):
    tipo_documento: str | None
    tipo_entidade: str
    
class AnexoRequest(AnexoBase):
    entidade_nome: str  

class AnexoResponse(AnexoBase):
    id: int
    nome_original: str
    nome_seguro: str
    data_upload: date
    id_entidade: int

    class Config:
        from_attributes = True