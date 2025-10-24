import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from datetime import date
from app.models.aocs_models import Aocs
from app.schemas.aocs_schema import AocsRequest
from .unidades_repository import UnidadesRepository
from .locais_repository import LocaisRepository
from .agentes_repository import AgentesRepository
from .dotacao_repository import DotacaoRepository


class AocsRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn
        self.unidades_repo = UnidadesRepository(db_conn)
        self.locais_repo = LocaisRepository(db_conn)
        self.agentes_repo = AgentesRepository(db_conn)
        self.dotacao_repo = DotacaoRepository(db_conn)

    #Mapear
    def _map_row_to_model(self, row: DictCursor) -> Aocs:

    #Monta a AOCS
        return Aocs(
            id=row['id'], 
            numero_aocs=row['numero_aocs'], 
            data_criacao=row['data_criacao'], 
            justificativa=row['justificativa'], 
            local_data=row['local_data'], 
            id_unidade_requisitante=row['id_unidade_requisitante'], 
            id_local_entrega=row['id_local_entrega'],
            id_agente_responsavel=row['id_agente_responsavel'],
            id_dotacao=row['id_dotacao'],
            numero_pedido=row.get('numero_pedido'),
            tipo_pedido=row.get('tipo_pedido'),
            empenho=row.get('empenho'),
        )
    
    #Criar
    def create(self, aocs_req: AocsRequest) -> Aocs:
        cursor = None
        try:
            #repositório
            uni = self.unidades_repo.get_by_nome(aocs_req.unidade_requisitante_nome)
            loc = self.locais_repo.get_by_nome(aocs_req.local_entrega_nome)
            age = self.agentes_repo.get_by_nome(aocs_req.agente_responsavel_nome)
            dot = self.dotacao_repo.get_by_nome(aocs_req.dotacao_nome)
                        
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO aocs (numero_aocs, justificativa, data_criacao, local_data, id_unidade_requisitante, id_local_entrega, id_agente_responsavel, id_dotacao, numero_pedido, tipo_pedido, empenho) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                RETURNING * """
                        
            cursor.execute(sql, (aocs_req.numero_aocs, aocs_req.justificativa, aocs_req.data_criacao, aocs_req.local_data, uni.id, loc.id, age.id, dot.id, aocs_req.numero_pedido, aocs_req.tipo_pedido, aocs_req.empenho))
            
            new_data = cursor.fetchone()
            self.db_conn.commit()
            
            return self._map_row_to_model(new_data)
        
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn:
                self.db_conn.rollback() 
            print(f"Erro ao criar aocs: {error}")
            raise 
        
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Aocs | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM aocs WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return self._map_row_to_model(data)
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #ListarGeral
    def get_all(self) -> list[Aocs]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
        
            sql = "SELECT * FROM aocs ORDER BY local_data"
        
            cursor.execute(sql)
    
            all_data = cursor.fetchall()
        
            return [self._map_row_to_model(row)
                    for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Buscar pela AOCS
    def get_by_aocs(self, numero_aocs: str) -> Aocs:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM aocs WHERE numero_aocs = %s"
            cursor.execute(sql, (numero_aocs,))
            data = cursor.fetchone()
            
            if data:
                return self._map_row_to_model(data)
            
            return None 
        finally:
            if cursor:
                cursor.close()
                
    #Atualizar
    def update(self, id: int, aocs_req: AocsRequest) -> Aocs | None:
        cursor = None
        try:
            #repositório
            uni = self.unidades_repo.get_by_nome(aocs_req.unidade_requisitante_nome)
            loc = self.locais_repo.get_by_nome(aocs_req.local_entrega_nome)
            age = self.agentes_repo.get_by_nome(aocs_req.agente_responsavel_nome)
            dot = self.dotacao_repo.get_by_nome(aocs_req.dotacao_nome)
            
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE aocs 
                SET 
                    numero_aocs = %s, 
                    justificativa = %s,
                    data_criacao = %s,
                    local_data = %s, 
                    id_unidade_requisitante = %s, 
                    id_local_entrega = %s, 
                    id_agente_responsavel = %s, 
                    id_dotacao = %s, 
                    numero_pedido = %s, 
                    tipo_pedido = %s, 
                    empenho = %s
                WHERE id = %s
                RETURNING *
            """
            
            params = (aocs_req.numero_aocs, aocs_req.justificativa, aocs_req.data_criacao, aocs_req.local_data, uni.id, loc.id, age.id, dot.id, aocs_req.numero_pedido, aocs_req.tipo_pedido, aocs_req.empenho, id)
            
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
            
            sql = "DELETE FROM aocs WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()