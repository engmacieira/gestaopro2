from pydantic import BaseModel

class AgentesBase(BaseModel):
    nome: str

class AgentesRequest(AgentesBase):
    pass  

class AgentesResponse(AgentesBase):
    id: int

    class Config:
        from_attributes = True