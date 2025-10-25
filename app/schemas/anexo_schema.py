from datetime import date
from pydantic import BaseModel, Field

class AnexoBase(BaseModel):
    id_entidade: int 
    tipo_entidade: str 
    tipo_documento: str | None = None 

class AnexoCreate(AnexoBase):    
    nome_original: str
    nome_seguro: str 
    data_upload: date = Field(default_factory=date.today) 

class AnexoResponse(AnexoBase):
    id: int
    nome_original: str
    nome_seguro: str 
    data_upload: date

    class Config:
        from_attributes = True