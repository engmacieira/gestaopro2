from pydantic import BaseModel, ConfigDict

class DescricaoItemBase(BaseModel):
    descricao: str

class DescricaoItemRequest(DescricaoItemBase): 
    pass

class DescricaoItemResponse(DescricaoItemBase): 
    
    model_config = ConfigDict(from_attributes=True)