from pydantic import BaseModel

class NumeromodalidadeBase(BaseModel):
    numero_ano: str
    
class NumeromodalidadeRequest(NumeromodalidadeBase):
    pass  

class NumeromodalidadeResponse(NumeromodalidadeBase):
    id: int

    class Config:
        from_attributes = True