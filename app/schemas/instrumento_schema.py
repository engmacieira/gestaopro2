from pydantic import BaseModel

class InstrumentoBase(BaseModel): 
    nome: str

class InstrumentoRequest(InstrumentoBase): 
    pass

class InstrumentoResponse(InstrumentoBase):
    id: int

    class Config:
        from_attributes = True