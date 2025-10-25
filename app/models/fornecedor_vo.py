class Fornecedor:
    def __init__(self,
                 nome: str,
                 cpf_cnpj: str | None = None,
                 email: str | None = None,
                 telefone: str | None = None):
        self.nome: str = nome
        self.cpf_cnpj: str | None = cpf_cnpj
        self.email: str | None = email
        self.telefone: str | None = telefone