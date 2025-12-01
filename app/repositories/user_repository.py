import psycopg2
from psycopg2.extensions import connection 
from psycopg2.extras import DictCursor 
from werkzeug.security import generate_password_hash 
import logging

from app.models.user_model import User
from app.schemas.user_schema import UserCreateRequest, UserUpdateRequest

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, db_conn):
        self.db_conn = db_conn
    
    def get_by_username(self, username: str) -> User | None:
        cursor = self.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sql = "SELECT * FROM usuarios WHERE username = %s AND ativo = TRUE"
        try:
            cursor.execute(sql, (username,))
            user_data = cursor.fetchone()
            
            if user_data:
                return User(
                    id=user_data['id'],
                    username=user_data['username'],
                    password_hash=user_data['password_hash'],
                    nivel_acesso=user_data['nivel_acesso'],
                    ativo=user_data['ativo']
                )
            
            return None 
            
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Erro ao buscar usuário: {error}")
            return None
        finally:
            if cursor:
                cursor.close()
                
    def get_by_id(self, user_id: int) -> User | None:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM usuarios WHERE id = %s AND ativo = TRUE" # Opcional: buscar só ativos?
            cursor.execute(sql, (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return User(
                    id=user_data['id'], username=user_data['username'],
                    password_hash=user_data['password_hash'], nivel_acesso=user_data['nivel_acesso'],
                    ativo=user_data['ativo']
                )
            return None
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Erro ao buscar usuário por ID: {error}")
            return None
        finally:
            if cursor: cursor.close()

    def get_all(self, skip: int = 0, limit: int = 100, mostrar_inativos: bool = False) -> list[User]:
        cursor = None
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = "SELECT * FROM usuarios"
            params = []
            if not mostrar_inativos:
                sql += " WHERE ativo = TRUE"
            sql += " ORDER BY username LIMIT %s OFFSET %s"
            params.extend([limit, skip])

            cursor.execute(sql, params)
            users_data = cursor.fetchall()
            return [
                User(id=u['id'], username=u['username'], password_hash=u['password_hash'],
                     nivel_acesso=u['nivel_acesso'], ativo=u['ativo'])
                for u in users_data
            ]
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Erro ao listar usuários: {error}")
            return []
        finally:
            if cursor: cursor.close()

    def create(self, user_create: UserCreateRequest) -> User:
        cursor = None
       
        hashed_password = generate_password_hash(user_create.password)
      
        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            sql = """
                INSERT INTO usuarios (username, password_hash, nivel_acesso, ativo)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            """
            cursor.execute(sql, (
                user_create.username,
                hashed_password, 
                user_create.nivel_acesso,
                user_create.ativo
            ))
            user_data = cursor.fetchone()
            self.db_conn.commit()
            return User(
                id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'],
                nivel_acesso=user_data['nivel_acesso'], ativo=user_data['ativo']
            )
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            print(f"Erro ao criar usuário: {error}")
            raise 
        finally:
            if cursor: cursor.close()

    def update(self, user_id: int, user_update: UserUpdateRequest) -> User | None:
        cursor = None
        
        fields_to_update = []
        params = []
        if user_update.username is not None:
            fields_to_update.append("username = %s")
            params.append(user_update.username)
        if user_update.nivel_acesso is not None:
            fields_to_update.append("nivel_acesso = %s")
            params.append(user_update.nivel_acesso)
        if user_update.ativo is not None:
            fields_to_update.append("ativo = %s")
            params.append(user_update.ativo)

        if not fields_to_update:
             return self.get_by_id(user_id)

        params.append(user_id) 

        try:
            cursor = self.db_conn.cursor(cursor_factory=DictCursor)
            set_clause = ", ".join(fields_to_update)
            sql = f"UPDATE usuarios SET {set_clause} WHERE id = %s RETURNING *"

            cursor.execute(sql, params)
            user_data = cursor.fetchone()
            self.db_conn.commit()

            if user_data:
                 return User(
                    id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'],
                    nivel_acesso=user_data['nivel_acesso'], ativo=user_data['ativo']
                 )
            return None 

        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            print(f"Erro ao atualizar usuário: {error}")
            raise
        finally:
            if cursor: cursor.close()

    def delete(self, user_id: int) -> bool:
        cursor = None
        try:
            cursor = self.db_conn.cursor()
            sql = "UPDATE usuarios SET ativo = FALSE WHERE id = %s"
            cursor.execute(sql, (user_id,))
            rowcount = cursor.rowcount
            self.db_conn.commit()
            return rowcount > 0 
        except (Exception, psycopg2.DatabaseError) as error:
            if self.db_conn: self.db_conn.rollback()
            print(f"Erro ao desativar usuário: {error}")
            return False
        finally:
            if cursor: cursor.close()

    def reset_password(self, user_id: int, new_password_hash: str) -> bool:
         cursor = None
         try:
             cursor = self.db_conn.cursor()
             sql = "UPDATE usuarios SET password_hash = %s WHERE id = %s"
             cursor.execute(sql, (new_password_hash, user_id))
             rowcount = cursor.rowcount
             self.db_conn.commit()
             return rowcount > 0
         except (Exception, psycopg2.DatabaseError) as error:
             if self.db_conn: self.db_conn.rollback()
             print(f"Erro ao resetar senha: {error}")
             return False
         finally:
             if cursor: cursor.close()
             
    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """Atualiza apenas a senha do usuário."""
        cursor = None
        try:
            cursor = self.db_conn.cursor()
            sql = "UPDATE usuarios SET password_hash = %s WHERE id = %s"
            cursor.execute(sql, (new_password_hash, user_id))
            self.db_conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            if self.db_conn: self.db_conn.rollback()
            logger.exception(f"Erro ao atualizar senha do usuário {user_id}: {e}")
            raise e
        finally:
            if cursor: cursor.close()