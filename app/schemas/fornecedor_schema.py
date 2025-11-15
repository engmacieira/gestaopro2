from pydantic import BaseModel, ConfigDict

class FornecedorBase(BaseModel):
    nome: str
    cpf_cnpj: str | None = None
    email: str | None = None
    telefone: str | None = None

class FornecedorRequest(FornecedorBase):
    pass

class FornecedorResponse(FornecedorBase):
    
    model_config = ConfigDict(from_attributes=True)