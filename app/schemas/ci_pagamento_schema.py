from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class CiPagamentoBase(BaseModel):
    numero_ci: str
    data_ci: date = Field(default_factory=date.today) 
    numero_nota_fiscal: str
    serie_nota_fiscal: str | None = None
    codigo_acesso_nota: str | None = None
    data_nota_fiscal: date
    valor_nota_fiscal: Decimal
    observacoes_pagamento: str | None = None

class CiPagamentoCreateRequest(CiPagamentoBase):
    aocs_numero: str 
    solicitante_nome: str 
    secretaria_nome: str 
    dotacao_info_orcamentaria: str 

class CiPagamentoUpdateRequest(BaseModel):
    numero_ci: str | None = None
    data_ci: date | None = None
    numero_nota_fiscal: str | None = None
    serie_nota_fiscal: str | None = None
    codigo_acesso_nota: str | None = None
    data_nota_fiscal: date | None = None
    valor_nota_fiscal: Decimal | None = None
    observacoes_pagamento: str | None = None
    aocs_numero: str | None = None
    solicitante_nome: str | None = None
    secretaria_nome: str | None = None
    dotacao_info_orcamentaria: str | None = None

class CiPagamentoResponse(CiPagamentoBase):
    id: int
    id_aocs: int
    id_pedido: int
    id_solicitante: int
    id_secretaria: int
    id_dotacao_pagamento: int

    model_config = ConfigDict(from_attributes=True)