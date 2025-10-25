from datetime import date
from app.models.fornecedor_vo import Fornecedor

class Contrato: 
    def __init__(self,
                 id: int,
                 id_categoria: int,
                 numero_contrato: str,
                 fornecedor_obj: Fornecedor,
                 data_inicio: date,
                 data_fim: date,
                 data_criacao: date,
                 ativo: bool,
                 id_instrumento_contratual: int,
                 id_modalidade: int,
                 id_numero_modalidade: int,
                 id_processo_licitatorio: int):
        self.id: int = id
        self.id_categoria: int = id_categoria
        self.numero_contrato: str = numero_contrato
        self.fornecedor: Fornecedor = fornecedor_obj
        self.data_inicio: date = data_inicio
        self.data_fim: date = data_fim
        self.data_criacao: date = data_criacao
        self.ativo: bool = ativo
        self.id_instrumento_contratual: int = id_instrumento_contratual
        self.id_modalidade: int = id_modalidade
        self.id_numero_modalidade: int = id_numero_modalidade
        self.id_processo_licitatorio: int = id_processo_licitatorio