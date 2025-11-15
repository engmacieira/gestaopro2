from pydantic import BaseModel, ConfigDict

class InstrumentoBase(BaseModel): 
    nome: str

class InstrumentoRequest(InstrumentoBase): 
    pass

class InstrumentoResponse(InstrumentoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)