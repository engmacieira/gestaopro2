from datetime import date

class Anexos:
    def __init__(self, id: int, id_entidade: int, nome_original: str, nome_seguro: str, data_upload: date, tipo_entidade: str, tipo_documento: str | None = None ):
        self.id: int = id
        self.id_entidade: int = id_entidade
        self.nome_original: str | None = nome_original
        self.nome_seguro: str = nome_seguro
        self.data_upload: date = data_upload
        self.tipo_documento: str = tipo_documento
        self.tipo_entidade: str = tipo_entidade