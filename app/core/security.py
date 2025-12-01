import os
import logging
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user_model import User
from app.repositories.user_repository import UserRepository
from app.core.database import get_db

logger = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

if not SECRET_KEY:
    raise ValueError("Variável de ambiente SECRET_KEY não definida.")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

def create_access_token(user: User | None = None, data: dict | None = None) -> str:
    to_encode = {}
    
    if user:
        to_encode = {
            "sub": user.username,
            "id": user.id,
            "nivel": user.nivel_acesso
        }
    elif data:
        to_encode = data.copy()
    else:
        raise ValueError("create_access_token precisa de 'user' ou 'data'")

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    request: Request, 
    token: str | None = Depends(oauth2_scheme), 
    db_conn = Depends(get_db)
) -> User:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        cookie_authorization = request.cookies.get("access_token")
        if cookie_authorization:
            scheme, _, param = cookie_authorization.partition(" ")
            if scheme.lower() == "bearer":
                token = param
            else:
                token = cookie_authorization 

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id") 
        
        if username is None or user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception 
    
    user_repo = UserRepository(db_conn)
    user = user_repo.get_by_id(user_id=user_id)
    
    if user is None:
        raise credentials_exception
        
    return user

def require_access_level(required_level: int):
    async def check_permission(current_user: User = Depends(get_current_user)) -> User:
        if current_user.nivel_acesso > required_level:
            logger.warning(f"Acesso negado: {current_user.username} tentou recurso nível {required_level}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para esta ação."
            )
        return current_user
    return check_permission

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return check_password_hash(hashed_password, plain_password)

def get_password_hash(password: str) -> str:
    return generate_password_hash(password)