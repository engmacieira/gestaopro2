import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from app.models.descricaoitem_vo import Descricaoitem
from app.models.itens_models import Itens
from app.schemas.itens_schema import ItensRequest
from .contratos_repository import ContratosRepository

class ItensRepository:
    def __init__(self, db_conn: connection):
        self.db_conn = db_conn
        self.contratos_repo = ContratosRepository(db_conn)

    #Mapear
    def _map_row_to_model(self, row: DictCursor) -> Itens:
    
    #Montar o Objeto de Valor Descricao
        descricao_obj = Descricaoitem(
            descricao=row['descricao'],
        )

    #Monta o Contrato
        return Itens(
            id=row['id'],
            id_contrato=row['id_contrato'],
            numero_item=row['numero_item'],
            unidade_medida=row['unidade_medida'], 
            quantidade=row['quantidade'], 
            valor_unitario=row['valor_unitario'], 
            ativo=row['ativo'], 
            marca=row.get('marca'),
            descricao_obj=descricao_obj
        )
    
    #Criar
    def create(self, itens_req: ItensRequest) -> Itens:
        cursor = None
        try:
            #repositório
            cont = self.contratos_repo.get_by_numero_contrato(itens_req.contrato_nome)
            
            desc_req = itens_req.descricao
            
            if not cont:
                raise ValueError(f"Contrato '{itens_req.contrato_nome}' não encontrado.")
            
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                INSERT INTO itenscontrato (id_contrato, numero_item, descricao, unidade_medida, quantidade, valor_unitario, ativo, marca) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
                RETURNING * """
                        
            cursor.execute(sql, (cont.id, itens_req.numero_item, desc_req.descricao, itens_req.unidade_medida, itens_req.quantidade, itens_req.valor_unitario, 
                                 True, itens_req.marca))
            
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
    def get_by_id(self, id: int) -> Itens | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM itenscontrato WHERE id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()
            
            if data:
                return self._map_row_to_model(data)
            
            return None 
        finally:
            if cursor:
                cursor.close()

    #Buscar itens pelo Contrato
    def get_by_contrato_id(self, id_contrato: int) -> list[Itens]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM itenscontrato WHERE id_contrato = %s"
            sql += " ORDER BY descricao" 
            cursor.execute(sql, (id_contrato,))
            all_data = cursor.fetchall()
            
            return [self._map_row_to_model(row) for row in all_data]
        
        finally:
            if cursor:
                cursor.close()
    
    #Buscar itens pela Descrição
    def get_by_descricao(self, descricao: str) -> Itens:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM itenscontrato WHERE descricao = %s"
            cursor.execute(sql, (descricao,))
            data = cursor.fetchone()
            
            if data:
                return self._map_row_to_model(data)
            
            return None 
        finally:
            if cursor:
                cursor.close()
    
    #ListarGeral
    def get_all(self, mostrar_inativos: bool = False) -> list[Itens]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = "SELECT * FROM itenscontrato"
            if not mostrar_inativos:
                sql += " WHERE ativo = TRUE"
            sql += " ORDER BY descricao"
            
            cursor.execute(sql)
            all_data = cursor.fetchall()
            
            return [self._map_row_to_model(row)
                    for row in all_data]
        finally:
            if cursor:
                cursor.close()

    #Atualizar
    def update(self, id: int, itens_req: ItensRequest) -> Itens | None:
        cursor = None
        try:
            #repositório
            cont = self.contratos_repo.get_by_numero_contrato(itens_req.contrato_nome)
            
            desc_req = itens_req.descricao
            
            if not cont:
                 raise ValueError(f"Contrato '{itens_req.contrato_nome}' não encontrado para atualização do item.")
                        
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            
            sql = """
                UPDATE itenscontrato 
                SET 
                    id_contrato = %s, 
                    numero_item = %s, 
                    descricao = %s, 
                    unidade_medida = %s, 
                    quantidade = %s, 
                    valor_unitario = %s, 
                    marca = %s
                WHERE id = %s
                RETURNING *
            """
            
            params = (cont.id, itens_req.numero_item, desc_req.descricao, itens_req.unidade_medida, itens_req.quantidade, itens_req.valor_unitario, 
                                itens_req.marca, id)
            
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
            
            sql = "DELETE FROM itenscontrato WHERE id = %s"
            cursor.execute(sql, (id,))
            
            rowcount = cursor.rowcount
            
            self.db_conn.commit()
            
            return rowcount > 0
        finally:
            if cursor:
                cursor.close()