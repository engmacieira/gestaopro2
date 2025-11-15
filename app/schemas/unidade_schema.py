from pydantic import BaseModel, ConfigDict

class UnidadeBase(BaseModel): 
    nome: str

class UnidadeRequest(UnidadeBase): 
    pass

class UnidadeResponse(UnidadeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)