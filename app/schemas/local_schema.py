from pydantic import BaseModel

class LocalBase(BaseModel): 
    descricao: str

class LocalRequest(LocalBase): 
    pass

class LocalResponse(LocalBase): 
    id: int

    class Config:
        from_attributes = True