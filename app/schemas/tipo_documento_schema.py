from pydantic import BaseModel

class TipoDocumentoBase(BaseModel): 
    nome: str

class TipoDocumentoRequest(TipoDocumentoBase): 
    pass

class TipoDocumentoResponse(TipoDocumentoBase):
    id: int

    class Config:
        from_attributes = True