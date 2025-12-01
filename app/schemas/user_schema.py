from pydantic import BaseModel, Field, ConfigDict 
from datetime import date

class UserBase(BaseModel):
    username: str
    nivel_acesso: int
    ativo: bool = True

class UserCreateRequest(UserBase):
    password: str = Field(..., min_length=8, description="A senha deve ter no mínimo 8 caracteres")

class UserUpdateRequest(BaseModel):
    username: str | None = None
    nivel_acesso: int | None = None
    ativo: bool | None = None

class UserResponse(UserBase):
    id: int
    data_criacao: date 

    model_config = ConfigDict(from_attributes=True)

class UserAdminResponse(UserResponse):
     data_criacao: date | None = None
     
class UserChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Senha atual para validação")
    new_password: str = Field(..., min_length=4, description="Nova senha desejada")