from pydantic import BaseModel

class ProcessolicitatorioBase(BaseModel):
    numero: str
    
class ProcessolicitatorioRequest(ProcessolicitatorioBase):
    pass  

class ProcessolicitatorioResponse(ProcessolicitatorioBase):
    id: int

    class Config:
        from_attributes = True