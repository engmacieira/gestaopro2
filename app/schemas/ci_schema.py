from datetime import date
from decimal import Decimal
from pydantic import BaseModel

class CiBase(BaseModel):
    numero_ci: str
    data_ci: date
    numero_nota_fiscal: str
    serie_nota_fiscal: str
    codigo_acesso_nota: str | None = None
    data_nota_fiscal: date  
    valor_nota_fiscal: Decimal 
    observacoes_pagamento: str | None = None

class CiRequest(CiBase):
    aocs_nome: str
    solicitante_nome: str
    secretaria_nome: str
    dotacao_pagamento_nome: str

class CiResponse(CiBase):
    id: int
    id_aocs: int
    id_solicitante: int
    id_secretaria: int
    id_dotacao_pagamento: int
    
    class Config:
        from_attributes = True