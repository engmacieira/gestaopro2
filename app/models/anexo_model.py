from datetime import date

class Anexo:
    def __init__(self,
                 id: int,
                 nome_original: str | None,
                 nome_seguro: str,
                 data_upload: date,
                 tipo_entidade: str,
                 tipo_documento: str | None = None,
                 id_contrato: int | None = None, 
                 id_aocs: int | None = None      
                 ):
        
        self.id: int = id
        self.nome_original: str | None = nome_original
        self.nome_seguro: str = nome_seguro 
        self.data_upload: date = data_upload
        self.tipo_documento: str | None = tipo_documento 
        self.tipo_entidade: str = tipo_entidade
        
        self.id_contrato: int | None = id_contrato
        self.id_aocs: int | None = id_aocs