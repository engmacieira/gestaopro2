from pydantic import BaseModel

class TiposdocumentosBase(BaseModel):
    nome: str
    
class TiposdocumentosRequest(TiposdocumentosBase):
    pass  

class TiposdocumentosResponse(TiposdocumentosBase):
    id: int

    class Config:
        from_attributes = True