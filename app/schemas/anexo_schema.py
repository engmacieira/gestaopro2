from datetime import date
from pydantic import BaseModel, Field, ConfigDict

class AnexoBase(BaseModel):
    id_entidade: int 
    tipo_entidade: str 
    tipo_documento: str | None = None 

class AnexoCreate(AnexoBase):    
    nome_original: str
    nome_seguro: str 
    data_upload: date = Field(default_factory=date.today)

class AnexoResponse(BaseModel): 
    id: int
    nome_original: str
    nome_seguro: str 
    data_upload: date
    tipo_documento: str | None
    tipo_entidade: str
    
    id_contrato: int | None = None 
    id_aocs: int | None = None

    model_config = ConfigDict(from_attributes=True)