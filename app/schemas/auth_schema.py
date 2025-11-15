from datetime import date
from pydantic import BaseModel, ConfigDict

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    
class UserResponse(BaseModel):
    id: int
    username: str
    nivel_acesso: int
    ativo: bool
    
    model_config = ConfigDict(from_attributes=True)