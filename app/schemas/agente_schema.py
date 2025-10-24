from pydantic import BaseModel

class AgenteBase(BaseModel): 
    nome: str

class AgenteRequest(AgenteBase): 
    pass 

class AgenteResponse(AgenteBase):
    id: int

    class Config:
        from_attributes = True 