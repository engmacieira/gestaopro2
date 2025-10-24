from datetime import datetime

class Logs:
    def __init__(self, id: int, time: datetime, id_usuario: int, acao: str, detalhes: str):
            self.id: int = id
            self.time: datetime = time
            self.id_usuario: int = id_usuario
            self.acao: str = acao
            self.detalhes: str = detalhes