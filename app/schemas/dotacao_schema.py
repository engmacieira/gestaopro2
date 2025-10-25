from pydantic import BaseModel

class DotacaoBase(BaseModel):
    info_orcamentaria: str

class DotacaoRequest(DotacaoBase):
    pass

class DotacaoResponse(DotacaoBase):
    id: int

    class Config:
        from_attributes = True