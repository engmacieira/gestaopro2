import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from psycopg2.extensions import connection  # Para type hint
from app.models.user_model import User
from app.repositories.user_repository import UserRepository
from app.core.database import get_db

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

if not SECRET_KEY:
    raise ValueError("Variável de ambiente SECRET_KEY não definida. Verifique seu .env")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

#CRACHÁ
def create_access_token(user: User) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
    token: str = Depends(oauth2_scheme), 
    db_conn: connection = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception 
    user_repo = UserRepository(db_conn)
    user = user_repo.get_by_username(username=username)
    if user is None:
        raise credentials_exception
    return user