from pydantic import BaseModel

class ProcessoLicitatorioBase(BaseModel): 
    numero: str 

class ProcessoLicitatorioRequest(ProcessoLicitatorioBase): 
    pass

class ProcessoLicitatorioResponse(ProcessoLicitatorioBase): 
    id: int

    class Config:
        from_attributes = True