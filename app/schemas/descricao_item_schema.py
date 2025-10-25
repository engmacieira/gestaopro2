from pydantic import BaseModel

class DescricaoItemBase(BaseModel):
    descricao: str

class DescricaoItemRequest(DescricaoItemBase): 
    pass

class DescricaoItemResponse(DescricaoItemBase): 
    
    class Config:
        from_attributes = True 