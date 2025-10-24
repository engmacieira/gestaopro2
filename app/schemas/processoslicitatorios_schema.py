from pydantic import BaseModel

class ProcessoslicitatoriosBase(BaseModel):
    numero: str
    
class ProcessoslicitatoriosRequest(ProcessoslicitatoriosBase):
    pass  

class ProcessoslicitatoriosResponse(ProcessoslicitatoriosBase):
    id: int

    class Config:
        from_attributes = True