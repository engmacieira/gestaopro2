from pydantic import BaseModel

class NumeroModalidadeBase(BaseModel): 
    numero_ano: str 

class NumeroModalidadeRequest(NumeroModalidadeBase): 
    pass

class NumeroModalidadeResponse(NumeroModalidadeBase): 
    id: int

    class Config:
        from_attributes = True