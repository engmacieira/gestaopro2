from datetime import datetime
from pydantic import BaseModel

class LogsBase(BaseModel):
    id: int
    time: datetime
    id_usuario: int
    acao: str
    detalhes: str
    
class LogsRequest(LogsBase):
    pass  

class LogsResponse(LogsBase):
    pass  

    class Config:
        from_attributes = True