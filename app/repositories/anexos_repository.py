import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from datetime import date
from app.models.anexos_models import Anexos
from app.schemas.anexos_schema import AnexosRequest
from .tiposdocumentos_repository import TiposdocumentosRepository


class AnexosRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn
        self.tiposdocumentos_repo = TiposdocumentosRepository(db_conn)

    #Mapear
    def _map_row_to_model(self, row: DictCursor) -> Anexos:

    #Monta a AOCS
        return Anexos(
            id=row['id'], 
            id_entidade=row['id_entidade'], 
            nome_original=row['nome_original'], 
            nome_seguro=row['nome_seguro'], 
            data_upload=row['data_upload'], 
            tipo_documento=row.get('tipo_documento'), 
            tipo_entidade=row['tipo_entidade']
        )
    
    #Criar
    def create(self, anexos_req: AnexosRequest) -> Anexos:
        cursor = None
        try:
            #repositório
            ent = self.tiposdocumentos_repo.get_by_nome(anexos_req.entidade_nome)

            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO anexos (id_entidade, tipo_documento, tipo_entidade)
                VALUES (%s, %s, %s) 
                RETURNING * """
                        
            cursor.execute(sql, (ent.id, anexos_req.tipo_documento, anexos_req.tipo_entidade)) 
            new_data = cursor.fetchone()
            self.db_conn.commit()
            
            return self._map_row_to_model(new_data)
        
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn:
                self.db_conn.rollback() 
            print(f"Erro ao criar anexos: {error}")
            raise 
        
        finally:
            if cursor:
                cursor.close()

    #Buscar pelo ID
    def get_by_id(self, id: int) -> Anexos | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM anexos WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return self._map_row_to_model(data)
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #ListarGeral
    def get_all(self) -> list[Anexos]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
        
            sql = "SELECT * FROM anexos ORDER BY data_upload"
        
            cursor.execute(sql)
    
            all_data = cursor.fetchall()
        
            return [self._map_row_to_model(row)
                    for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Atualizar
    def update(self, id: int, anexos_req: AnexosRequest) -> Anexos | None:
        cursor = None
        try:
            #repositório
            aoc = self.tiposdocumentos_repo.get_by_nome(anexos_req.entidade_nome)
            
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE anexos 
                SET 
                    id_entidade = %s, 
                    tipo_documento = %s, 
                    tipo_entidade = %s
                WHERE id = %s
                RETURNING *
            """
            
            params = (aoc.id, anexos_req.tipo_documento, anexos_req.tipo_entidade, id)
            
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
            
            sql = "DELETE FROM anexos WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()