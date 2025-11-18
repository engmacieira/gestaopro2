from datetime import date
from decimal import Decimal

class CiPagamento: 
    def __init__(self,
                 id: int,
                 id_aocs: int,
                 id_pedido: int,
                 numero_ci: str,
                 data_ci: date,
                 numero_nota_fiscal: str,
                 serie_nota_fiscal: str | None,
                 data_nota_fiscal: date,
                 valor_nota_fiscal: Decimal,
                 id_dotacao_pagamento: int,
                 id_solicitante: int, 
                 id_secretaria: int, 
                 observacoes_pagamento: str | None = None,
                 codigo_acesso_nota: str | None = None):
        self.id: int = id
        self.id_aocs: int = id_aocs
        self.id_pedido: int = id_pedido
        self.numero_ci: str = numero_ci
        self.data_ci: date = data_ci
        self.numero_nota_fiscal: str = numero_nota_fiscal
        self.serie_nota_fiscal: str | None = serie_nota_fiscal
        self.codigo_acesso_nota: str | None = codigo_acesso_nota
        self.data_nota_fiscal: date = data_nota_fiscal
        self.valor_nota_fiscal: Decimal = valor_nota_fiscal
        self.id_dotacao_pagamento: int = id_dotacao_pagamento
        self.observacoes_pagamento: str | None = observacoes_pagamento
        self.id_solicitante: int = id_solicitante
        self.id_secretaria: int = id_secretaria