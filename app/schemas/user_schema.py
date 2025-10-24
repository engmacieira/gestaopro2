from datetime import date
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    password_hash: str
    nivel_acesso: int
    
class UserRequest(UserBase):
    pass  

class UserResponse(UserBase):
    id: int
    ativo: bool
    data_criacao: date

    class Config:
        from_attributes = True