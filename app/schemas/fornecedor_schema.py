from pydantic import BaseModel

class FornecedorBase(BaseModel):
    nome: str
    cpf_cnpj: str | None = None
    email: str | None = None
    telefone: str | None = None

class FornecedorRequest(FornecedorBase):
    pass

class FornecedorResponse(FornecedorBase):
    
    class Config:
        from_attributes = True