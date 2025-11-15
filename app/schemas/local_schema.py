from pydantic import BaseModel, ConfigDict

class LocalBase(BaseModel): 
    descricao: str

class LocalRequest(LocalBase): 
    pass

class LocalResponse(LocalBase): 
    id: int

    model_config = ConfigDict(from_attributes=True)