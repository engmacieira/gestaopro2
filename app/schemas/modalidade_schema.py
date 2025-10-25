from pydantic import BaseModel

class ModalidadeBase(BaseModel):
    nome: str

class ModalidadeRequest(ModalidadeBase):
    pass

class ModalidadeResponse(ModalidadeBase):
    id: int

    class Config:
        from_attributes = True