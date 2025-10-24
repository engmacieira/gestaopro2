from pydantic import BaseModel

class UnidadesBase(BaseModel):
    nome: str
    
class UnidadesRequest(UnidadesBase):
    pass  

class UnidadesResponse(UnidadesBase):
    id: int

    class Config:
        from_attributes = True