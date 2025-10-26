import os
import logging
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from psycopg2.extensions import connection 
from app.models.user_model import User
from app.repositories.user_repository import UserRepository
from app.core.database import get_db

logger = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

if not SECRET_KEY:
    logger.critical("Variável de ambiente SECRET_KEY não definida!")
    raise ValueError("Variável de ambiente SECRET_KEY não definida. Verifique seu .env")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

#CRACHÁ
def create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data_to_encode = {
        "sub": user.username,
        "id": user.id,
        "nivel": user.nivel_acesso,
        "exp": expire
    }
    encoded_jwt = jwt.encode(data_to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

#PORTEIRO
def get_current_user(
    token_header: str | None = Depends(oauth2_scheme), # Agora pode ser None
    access_token_cookie: str | None = Cookie(None, alias="access_token"), # Também é bom ser explícito que pode ser None
    db_conn: connection = Depends(get_db)) -> User:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Lógica de extração: Prioriza o Header (token_header), senão usa o Cookie.
    token = token_header if token_header else access_token_cookie

    if not token:
        raise credentials_exception
    
    # Remove o prefixo "bearer " se estiver presente (está no cookie e no header)
    if token.lower().startswith("bearer "):
        token = token.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id") # Boa prática pegar o ID também
        if username is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception 
    
    user_repo = UserRepository(db_conn)
    user = user_repo.get_by_id(user_id=user_id)
    
    if user is None:
        raise credentials_exception
    return user

#NIVEL DE ACESSO
def require_access_level(required_level: int):
    async def check_permission(current_user: User = Depends(get_current_user)) -> User:
        if current_user.nivel_acesso > required_level:
            logger.warning(f"Acesso negado para usuário '{current_user.username}' (Nível {current_user.nivel_acesso}) à recurso de Nível {required_level}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para realizar esta ação."
            )
        return current_user 
    return check_permission
    
require_admin = require_access_level(1)
require_editor = require_access_level(2)
require_viewer = require_access_level(3)