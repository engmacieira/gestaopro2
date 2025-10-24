from pydantic import BaseModel

class CategoriaBase(BaseModel):
    nome: str

class CategoriaRequest(CategoriaBase):
    pass  

class CategoriaResponse(CategoriaBase):
    id: int
    ativo: bool 

    class Config:
        from_attributes = True