from werkzeug.security import check_password_hash

class User:
    def __init__(self, id: int, username: str, password_hash: str, nivel_acesso: int, ativo: bool):
        self.id: int = id 
        self.username: str = username
        self.password_hash: str = password_hash
        self.nivel_acesso: int = nivel_acesso 
        self.ativo: bool = ativo

    def verificar_senha (self, senha_pura: str) -> bool:
        return check_password_hash(self.password_hash, senha_pura)