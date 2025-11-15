from pydantic import BaseModel, ConfigDict

class ModalidadeBase(BaseModel):
    nome: str

class ModalidadeRequest(ModalidadeBase):
    pass

class ModalidadeResponse(ModalidadeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)