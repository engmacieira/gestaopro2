from pydantic import BaseModel

class InstrumentosBase(BaseModel):
    nome: str
    
class InstrumentosRequest(InstrumentosBase):
    pass  

class InstrumentosResponse(InstrumentosBase):
    id: int

    class Config:
        from_attributes = True