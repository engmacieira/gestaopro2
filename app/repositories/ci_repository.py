import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from datetime import date
from app.models.ci_models import Ci
from app.schemas.ci_schema import CiRequest
from .aocs_repository import AocsRepository
from .agentes_repository import AgentesRepository
from .unidades_repository import UnidadesRepository
from .dotacao_repository import DotacaoRepository

class CiRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn
        self.aocs_repo = AocsRepository(db_conn)
        self.agentes_repo = AgentesRepository(db_conn)
        self.unidades_repo = UnidadesRepository(db_conn)
        self.dotacao_repo = DotacaoRepository(db_conn)

    #Mapear
    def _map_row_to_model(self, row: DictCursor) -> Ci:

    #Monta a AOCS
        return Ci(
            id=row['id'], 
            id_aocs=row['id_aocs'], 
            numero_ci=row['numero_ci'], 
            data_ci=row['data_ci'], 
            numero_nota_fiscal=row['numero_nota_fiscal'], 
            serie_nota_fiscal=row['serie_nota_fiscal'], 
            codigo_acesso_nota=row.get('codigo_acesso_nota'),
            data_nota_fiscal=row['data_nota_fiscal'], 
            valor_nota_fiscal=row['valor_nota_fiscal'], 
            id_dotacao_pagamento=row['id_dotacao_pagamento'], 
            observacoes_pagamento=row.get('observacoes_pagamento'), 
            id_solicitante=row['id_solicitante'], 
            id_secretaria=row['id_secretaria']
        )
    
    #Criar
    def create(self, ci_req: CiRequest) -> Ci:
        cursor = None
        try:
            #repositório
            aoc = self.aocs_repo.get_by_aocs(ci_req.aocs_nome)
            age = self.agentes_repo.get_by_nome(ci_req.solicitante_nome)
            uni = self.unidades_repo.get_by_nome(ci_req.secretaria_nome)
            dot = self.dotacao_repo.get_by_nome(ci_req.dotacao_pagamento_nome)
                        
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO ci_pagamento (id_aocs, numero_ci, data_ci, numero_nota_fiscal, serie_nota_fiscal, codigo_acesso_nota, data_nota_fiscal, valor_nota_fiscal, id_dotacao_pagamento, observacoes_pagamento, id_solicitante, id_secretaria)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                RETURNING * """
                        
            cursor.execute(sql, (aoc.id, ci_req.numero_ci, ci_req.data_ci, ci_req.numero_nota_fiscal, ci_req.serie_nota_fiscal, ci_req.codigo_acesso_nota, ci_req.data_nota_fiscal, ci_req.valor_nota_fiscal, dot.id, ci_req.observacoes_pagamento, age.id, uni.id)) 
            new_data = cursor.fetchone()
            self.db_conn.commit()
            
            return self._map_row_to_model(new_data)
        
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn:
                self.db_conn.rollback() 
            print(f"Erro ao criar ci: {error}")
            raise 
        
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Ci | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM ci_pagamento WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return self._map_row_to_model(data)
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #ListarGeral
    def get_all(self) -> list[Ci]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
        
            sql = "SELECT * FROM ci_pagamento ORDER BY numero_ci"
        
            cursor.execute(sql)
    
            all_data = cursor.fetchall()
        
            return [self._map_row_to_model(row)
                    for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Atualizar
    def update(self, id: int, ci_req: CiRequest) -> Ci | None:
        cursor = None
        try:
            #repositório
            aoc = self.aocs_repo.get_by_aocs(ci_req.aocs_nome)
            age = self.agentes_repo.get_by_nome(ci_req.solicitante_nome)
            uni = self.unidades_repo.get_by_nome(ci_req.secretaria_nome)
            dot = self.dotacao_repo.get_by_nome(ci_req.dotacao_pagamento_nome)
            
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE ci_pagamento 
                SET 
                    id_aocs = %s, 
                    numero_ci = %s, 
                    data_ci = %s, 
                    numero_nota_fiscal = %s, 
                    serie_nota_fiscal = %s, 
                    codigo_acesso_nota = %s, 
                    data_nota_fiscal = %s, 
                    valor_nota_fiscal = %s, 
                    id_dotacao_pagamento = %s, 
                    observacoes_pagamento = %s, 
                    id_solicitante = %s, 
                    id_secretaria = %s
                WHERE id = %s
                RETURNING *
            """
            
            params = (aoc.id, ci_req.numero_ci, ci_req.data_ci, ci_req.numero_nota_fiscal, ci_req.serie_nota_fiscal, ci_req.codigo_acesso_nota, ci_req.data_nota_fiscal, ci_req.valor_nota_fiscal, dot.id, ci_req.observacoes_pagamento, age.id, uni.id, id)
            
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
            
            sql = "DELETE FROM ci_pagamento WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()