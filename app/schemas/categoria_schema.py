from pydantic import BaseModel, ConfigDict

class CategoriaBase(BaseModel):
    nome: str

class CategoriaRequest(CategoriaBase):
    pass

class CategoriaResponse(CategoriaBase):
    id: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)