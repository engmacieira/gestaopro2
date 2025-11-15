from pydantic import BaseModel, ConfigDict

class TipoDocumentoBase(BaseModel): 
    nome: str

class TipoDocumentoRequest(TipoDocumentoBase): 
    pass

class TipoDocumentoResponse(TipoDocumentoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)