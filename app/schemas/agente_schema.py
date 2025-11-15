from pydantic import BaseModel, ConfigDict

class AgenteBase(BaseModel): 
    nome: str

class AgenteRequest(AgenteBase): 
    pass 

class AgenteResponse(AgenteBase):
    id: int

    model_config = ConfigDict(from_attributes=True)