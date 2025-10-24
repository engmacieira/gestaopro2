from pydantic import BaseModel

class UnidadeBase(BaseModel):
    nome: str
    
class UnidadeRequest(UnidadeBase):
    pass  

class UnidadeResponse(UnidadeBase):
    id: int

    class Config:
        from_attributes = True