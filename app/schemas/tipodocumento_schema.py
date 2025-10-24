from pydantic import BaseModel

class TipodocumentoBase(BaseModel):
    nome: str
    
class TipodocumentoRequest(TipodocumentoBase):
    pass  

class TipodocumentoResponse(TipodocumentoBase):
    id: int

    class Config:
        from_attributes = True