from pydantic import BaseModel

class LocaisBase(BaseModel):
    descricao: str
    
class LocaisRequest(LocaisBase):
    pass  

class LocaisResponse(LocaisBase):
    id: int

    class Config:
        from_attributes = True