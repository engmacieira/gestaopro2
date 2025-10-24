import psycopg2
from app.models.user_models import User

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