from pydantic import BaseModel, ConfigDict

class DotacaoBase(BaseModel):
    info_orcamentaria: str

class DotacaoRequest(DotacaoBase):
    pass

class DotacaoResponse(DotacaoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)