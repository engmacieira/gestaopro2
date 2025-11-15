from pydantic import BaseModel, ConfigDict

class NumeroModalidadeBase(BaseModel): 
    numero_ano: str 

class NumeroModalidadeRequest(NumeroModalidadeBase): 
    pass

class NumeroModalidadeResponse(NumeroModalidadeBase): 
    id: int

    model_config = ConfigDict(from_attributes=True)