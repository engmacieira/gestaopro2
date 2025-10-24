import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from datetime import date
from app.models.contrato_model import Contrato
from app.models.fornecedor_vo import Fornecedor
from app.schemas.contrato_schema import ContratoRequest
from .categoria_repository import CategoriaRepository
from .instrumento_repository import InstrumentoRepository
from .modalidade_repository import ModalidadeRepository
from .numeromodalidade_repository import NumeromodalidadeRepository
from .processolicitatorio_repository import ProcessolicitatorioRepository

class ContratoRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn
        self.categoria_repo = CategoriaRepository(db_conn)
        self.instrumentos_repo = InstrumentoRepository(db_conn)
        self.modalidade_repo = ModalidadeRepository(db_conn)
        self.numeromodalidade_repo = NumeromodalidadeRepository(db_conn)
        self.processoslicitatorios_repo = ProcessolicitatorioRepository(db_conn)

    #Mapear
    def _map_row_to_model(self, row: DictCursor) -> Contrato:
    #Montar o Objeto de Valor Fornecdor
        fornecedor_obj = Fornecedor(
            nome=row['fornecedor'],
            cpf_cnpj=row.get('cpf_cnpj'),
            email=row.get('email'),
            telefone=row.get('telefone')
        )
    #Monta o Contrato
        return Contrato(
            id=row['id'],
            id_categoria=row['id_categoria'],
            numero_contrato=row['numero_contrato'],
            data_inicio=row['data_inicio'],
            data_fim=row['data_fim'],
            data_criacao=row['data_criacao'],
            ativo=row['ativo'],
            id_instrumento_contratual=row['id_instrumento_contratual'],
            id_modalidade=row['id_modalidade'],
            id_numero_modalidade=row['id_numero_modalidade'],
            id_processo_licitatorio=row['id_processo_licitatorio'],
            fornecedor_obj=fornecedor_obj
        )
    
    #Criar
    def create(self, contratos_req: ContratoRequest) -> Contrato:
        cursor = None
        try:
            #repositório
            cat = self.categoria_repo.get_or_create(contratos_req.categoria_nome)
            inst = self.instrumentos_repo.get_or_create(contratos_req.instrumento_nome)
            mod = self.modalidade_repo.get_or_create(contratos_req.modalidade_nome)
            num_mod = self.numeromodalidade_repo.get_or_create(contratos_req.numero_modalidade_nome)
            proc = self.processoslicitatorios_repo.get_or_create(contratos_req.processo_licitatorio_nome)
            
            forn_req = contratos_req.fornecedor
            
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO contratos (id_categoria, numero_contrato, fornecedor, cpf_cnpj, email, telefone,
                    data_inicio, data_fim, data_criacao, ativo, id_instrumento_contratual, id_modalidade, 
                    id_numero_modalidade, id_processo_licitatorio) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                RETURNING * """
            
            cursor.execute(sql, (cat.id, contratos_req.numero_contrato, forn_req.nome, forn_req.cpf_cnpj, forn_req.email, forn_req.telefone,
                contratos_req.data_inicio, contratos_req.data_fim, date.today(), True, inst.id, mod.id, num_mod.id, proc.id))
            
            new_data = cursor.fetchone()
            self.db_conn.commit()
            
            return self._map_row_to_model(new_data)
        
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn:
                self.db_conn.rollback() 
            print(f"Erro ao criar contrato: {error}")
            raise 
        
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Contrato | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM contratos WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return self._map_row_to_model(data)
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #Busca pelo numero do contrato                
    def get_by_numero_contrato(self, numero_contrato: str) -> Contrato | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM contratos WHERE numero_contrato = %s"
            cursor.execute(sql, (numero_contrato,))
            data = cursor.fetchone()
            
            if data:
                return self._map_row_to_model(data)
            
            return None
        finally:
            if cursor:
                cursor.close()

    #Listar
    def get_all(self, mostrar_inativos: bool = False) -> list[Contrato]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM contratos"
            if not mostrar_inativos:
                sql += " WHERE ativo = TRUE"
            sql += " ORDER BY numero_contrato"
            
            cursor.execute(sql)
            all_data = cursor.fetchall()
            
            return [self._map_row_to_model(row)
                    for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Atualizar
    def update(self, id: int, contratos_req: ContratoRequest) -> Contrato | None:
        cursor = None
        try:
            #repositório
            cat = self.categoria_repo.get_or_create(contratos_req.categoria_nome)
            inst = self.instrumentos_repo.get_or_create(contratos_req.instrumento_nome)
            mod = self.modalidade_repo.get_or_create(contratos_req.modalidade_nome)
            num_mod = self.numeromodalidade_repo.get_or_create(contratos_req.numero_modalidade_nome)
            proc = self.processoslicitatorios_repo.get_or_create(contratos_req.processo_licitatorio_nome)
            
            forn_req = contratos_req.fornecedor
                        
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE contratos 
                SET 
                    id_categoria = %s, 
                    numero_contrato = %s, 
                    fornecedor = %s, 
                    cpf_cnpj = %s, 
                    email = %s, 
                    telefone = %s,
                    data_inicio = %s, 
                    data_fim = %s, 
                    id_instrumento_contratual = %s, 
                    id_modalidade = %s, 
                    id_numero_modalidade = %s, 
                    id_processo_licitatorio = %s
                WHERE id = %s
                RETURNING *
            """
            
            params = (cat.id, contratos_req.numero_contrato, forn_req.nome, forn_req.cpf_cnpj, forn_req.email, forn_req.telefone,
                contratos_req.data_inicio, contratos_req.data_fim, inst.id, mod.id, num_mod.id, proc.id, id)
            
            cursor.execute(sql, (params))
            updated_data = cursor.fetchone()
            
            self.db_conn.commit()
            
            if updated_data:
                return self._map_row_to_model(updated_data)
            
            return None
        
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn:
                self.db_conn.rollback()
            print(f"Erro ao atualizar contrato: {error}")
            raise
        
        finally:
            if cursor:
                cursor.close()

    #Excluir
    def delete(self, id: int) -> bool:
        cursor = None
        try:
            cursor = self.db_conn.cursor()
            
            sql = "DELETE FROM contratos WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()