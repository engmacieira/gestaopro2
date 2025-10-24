from pydantic import BaseModel

class ModalidadeBase(BaseModel):
    nome: str
    
class ModalidadeRequest(ModalidadeBase):
    pass  

class ModalidadeResponse(ModalidadeBase):
    id: int
    pass

    class Config:
        from_attributes = True