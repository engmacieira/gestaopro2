from pydantic import BaseModel, ConfigDict

class ProcessoLicitatorioBase(BaseModel): 
    numero: str 

class ProcessoLicitatorioRequest(ProcessoLicitatorioBase): 
    pass

class ProcessoLicitatorioResponse(ProcessoLicitatorioBase): 
    id: int

    model_config = ConfigDict(from_attributes=True)