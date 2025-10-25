from datetime import date

class Aocs:
    def __init__(self,
                 id: int,
                 numero_aocs: str,
                 data_criacao: date,
                 justificativa: str,
                 id_unidade_requisitante: int,
                 id_local_entrega: int,
                 id_agente_responsavel: int,
                 id_dotacao: int,
                 numero_pedido: str | None = None,
                 tipo_pedido: str | None = None, 
                 empenho: str | None = None):
        self.id: int = id
        self.numero_aocs: str = numero_aocs
        self.data_criacao: date = data_criacao
        self.justificativa: str = justificativa
        self.id_unidade_requisitante: int = id_unidade_requisitante
        self.id_local_entrega: int = id_local_entrega
        self.id_agente_responsavel: int = id_agente_responsavel
        self.id_dotacao: int = id_dotacao
        self.numero_pedido: str | None = numero_pedido
        self.tipo_pedido: str | None = tipo_pedido
        self.empenho: str | None = empenho