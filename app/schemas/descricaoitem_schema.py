from pydantic import BaseModel

class DescricaoitemBase(BaseModel):
    descricao: str 
    
class DescricaoitemRequest(DescricaoitemBase):
    pass  

class DescricaoitemResponse(DescricaoitemBase):
    pass

    class Config:
        from_attributes = True